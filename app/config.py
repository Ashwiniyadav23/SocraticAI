from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    DATABASE_URL: str = "postgresql+asyncpg://socratic:socratic@localhost:5432/socratic"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://socratic:socratic@localhost:5432/socratic"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM (OpenAI-compatible - point at any free-tier provider)
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_MODEL_FAST: str = "llama-3.1-8b-instant"
    LLM_API_KEY: str = "REPLACE_ME"

    ENV: str = "development"
    MAX_AGENT_CALLS_PER_TURN: int = 4
    AGENT_TIMEOUT_SECONDS: int = 6


settings = Settings()
