#!/bin/bash
# Raphael — Super Powerful Autonomous AI Assistant
# Start script

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ⚡ RAPHAEL ⚡                              ║"
echo "║           Super Powerful Autonomous AI Assistant             ║"
echo "║              \"I have no strings on me...\"                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

MODE="${1:-api}"

case "$MODE" in
    api)
        echo -e "${GREEN}Starting Raphael API server...${NC}"
        echo -e "${YELLOW}API: http://localhost:8000${NC}"
        echo -e "${YELLOW}Docs: http://localhost:8000/docs${NC}"
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    cli)
        echo -e "${GREEN}Starting Raphael CLI...${NC}"
        python -m app.cli.main
        ;;
    chat)
        echo -e "${GREEN}Starting Raphael Chat...${NC}"
        python -m app.cli.main chat
        ;;
    test)
        echo -e "${GREEN}Running tests...${NC}"
        python -m pytest tests/ -v --ignore=tests/test_vector_memory.py
        ;;
    test-all)
        echo -e "${GREEN}Running all tests (including vector memory - may download models)...${NC}"
        python -m pytest tests/ -v
        ;;
    health)
        echo -e "${GREEN}Checking system health...${NC}"
        python -c "
from app.llm.factory import list_providers
print('✅ LLM Providers:', list_providers())
from app.memory.vector_memory import VectorMemory
try:
    m = VectorMemory()
    print('✅ Vector Memory:', m.count(), 'entries')
except Exception as e:
    print('⚠️  Vector Memory:', e)
from app.agents.specialized import ResearchAgent, CodeAgent, SystemAgent, MemoryAgent
print('✅ Agents: Research, Code, System, Memory')
from app.orchestration import SupervisorAgent, SwarmManager
print('✅ Orchestration: Supervisor, Swarm')
print('✅ All systems operational')
        "
        ;;
    *)
        echo "Usage: ./run.sh [api|cli|chat|test|test-all|health]"
        echo ""
        echo "  api        Start the REST API server (default)"
        echo "  cli        Start the interactive CLI"
        echo "  chat       Start an interactive chat session"
        echo "  test       Run tests (excluding vector memory)"
        echo "  test-all   Run all tests"
        echo "  health     Check system health"
        ;;
esac
