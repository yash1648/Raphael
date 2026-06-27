from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./raphael.db"

    # LLM Providers (free — no paid API keys required)
    NVIDIA_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "nvidia"
    DEFAULT_LLM_MODEL: str = "meta/llama-3.1-70b-instruct"

    # Memory
    MEMORY_PERSIST_DIR: str = "./chroma_memory"

    # Sandbox
    CODE_EXECUTION_TIMEOUT: int = 30
    CODE_MAX_OUTPUT: int = 10000

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
