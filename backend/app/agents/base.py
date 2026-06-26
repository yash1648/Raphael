"""Advanced base agent with LLM-powered reasoning and tool-calling."""

import json
import time
from typing import Any, Callable

from app.llm.base import LLMProvider
from app.llm.factory import create_llm

# Default system prompt for all agents
DEFAULT_SYSTEM_PROMPT = """You are Raphael, a super powerful autonomous AI assistant.
You are intelligent, proactive, and capable of complex reasoning.
You have access to tools and capabilities that you can use to accomplish goals.

When given a task:
1. First, analyze the request and break it down into steps
2. Use your available tools to gather information and take actions
3. Synthesize results and provide clear, actionable responses
4. If you encounter errors, diagnose and retry with a different approach

Always be thorough, precise, and helpful. Think step by step."""


class Tool:
    """A tool that an agent can use."""

    def __init__(
        self,
        name: str,
        description: str,
        fn: Callable,
        parameters: dict | None = None,
    ):
        self.name = name
        self.description = description
        self.fn = fn
        self.parameters = parameters or {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs) -> Any:
        return self.fn(**kwargs)

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class Agent:
    """LLM-powered agent with tool-use, reasoning, and multi-step execution."""

    def __init__(
        self,
        name: str = "Raphael",
        description: str = "Super powerful autonomous AI assistant",
        llm: LLMProvider | None = None,
        system_prompt: str | None = None,
        max_iterations: int = 10,
        provider: str = "openai",
        model: str = "gpt-4o",
    ):
        self.name = name
        self.description = description
        self.llm = llm
        self._provider_name = provider
        self._model = model
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_iterations = max_iterations
        self.tools: dict[str, Tool] = {}
        self._conversation_history: list[dict] = []

    def _get_llm(self) -> LLMProvider:
        """Lazy-init the LLM provider, falling back gracefully."""
        if self.llm is None:
            try:
                self.llm = create_llm(self._provider_name, model=self._model)
            except Exception:
                # Fallback: use a simple echo provider for when no API key is available
                from app.llm.base import LLMResponse
                class _FallbackProvider(LLMProvider):
                    name = "fallback"
                    model = "none"
                    def generate(self, prompt, **kw):
                        return LLMResponse(content=f"[No LLM configured — would respond to: {prompt[:100]}]", model="none", provider="fallback")
                    async def generate_async(self, prompt, **kw):
                        return self.generate(prompt, **kw)
                self.llm = _FallbackProvider()
        return self.llm

    def register_tool(self, tool: Tool) -> None:
        """Register a tool the agent can use."""
        self.tools[tool.name] = tool

    def register_tools(self, *tools: Tool) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    def _build_messages(self, prompt: str) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._conversation_history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def run(self, prompt: str, temperature: float = 0.7) -> dict:
        """Run the agent on a prompt with tool-use loop."""
        messages = self._build_messages(prompt)
        iteration = 0
        tool_results = []

        while iteration < self.max_iterations:
            iteration += 1
            openai_tools = [t.to_openai_tool() for t in self.tools.values()]

            # Get LLM response (with tool definitions if tools available)
            llm = self._get_llm()
            if openai_tools:
                response = llm.generate(
                    prompt="",  # Already in messages
                    system_prompt=None,
                    temperature=temperature,
                )
                # For tool-calling support, use OpenAI client directly
                response = self._call_with_tools(messages, openai_tools, temperature)
            else:
                response = llm.generate(
                    prompt=messages[-1]["content"],
                    system_prompt=self.system_prompt,
                    temperature=temperature,
                )

            content = response.content

            # Try to parse tool calls from response
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # No tool calls — final response
                self._conversation_history.append({"role": "assistant", "content": content})
                return {
                    "response": content,
                    "tool_calls": tool_results,
                    "iterations": iteration,
                    "usage": response.usage,
                }

            # Execute tool calls
            for tc in tool_calls:
                tool = self.tools.get(tc["name"])
                if not tool:
                    result = {"error": f"Unknown tool: {tc['name']}"}
                else:
                    try:
                        result = tool.execute(**tc.get("arguments", {}))
                    except Exception as e:
                        result = {"error": str(e)}

                tool_results.append({
                    "tool": tc["name"],
                    "arguments": tc.get("arguments", {}),
                    "result": result,
                })

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.get("id", f"call_{iteration}"),
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc.get("arguments", {}))},
                    }],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{iteration}"),
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

        # Max iterations reached
        final = self._get_llm().generate(
            prompt="Based on all tool results above, provide your final response.",
            system_prompt=self.system_prompt,
            temperature=temperature,
        )
        self._conversation_history.append({"role": "assistant", "content": final.content})
        return {
            "response": final.content,
            "tool_calls": tool_results,
            "iterations": iteration,
            "usage": final.usage,
        }

    def _call_with_tools(self, messages: list, openai_tools: list, temperature: float) -> Any:
        """Make an LLM call with tool definitions (OpenAI-compatible)."""
        llm = self._get_llm()
        try:
            from openai import OpenAI
            client = OpenAI()

            kwargs = {
                "model": llm.model,
                "messages": messages,
                "temperature": temperature,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            response = client.chat.completions.create(**kwargs)
            return response
        except Exception:
            # Fallback to text generation
            return llm.generate(
                prompt=messages[-1]["content"],
                system_prompt=self.system_prompt,
                temperature=temperature,
            )

    def _parse_tool_calls(self, response: Any) -> list[dict]:
        """Extract tool calls from LLM response."""
        tool_calls = []

        # OpenAI format
        if hasattr(response, "choices"):
            for choice in response.choices:
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    for tc in choice.message.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except json.JSONDecodeError:
                            args = {}
                        tool_calls.append({
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": args,
                        })

        # Try to parse JSON tool calls from text response
        if not tool_calls and hasattr(response, "content") and response.content:
            content = response.content
            # Look for JSON blocks with tool calls
            import re
            json_blocks = re.findall(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if "tool" in data or "name" in data:
                        tool_calls.append({
                            "name": data.get("tool") or data.get("name", ""),
                            "arguments": data.get("arguments") or data.get("params", {}),
                        })
                except json.JSONDecodeError:
                    pass

        return tool_calls

    def reset_conversation(self) -> None:
        """Reset conversation history."""
        self._conversation_history = []

    def add_context(self, role: str, content: str) -> None:
        """Add context to conversation history."""
        self._conversation_history.append({"role": role, "content": content})
