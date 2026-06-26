from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./raphael.db"

    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-4o"

    # Memory
    MEMORY_PERSIST_DIR: str = "./chroma_memory"

    # Sandbox
    CODE_EXECUTION_TIMEOUT: int = 30
    CODE_MAX_OUTPUT: int = 10000

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
