from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INSURANCE_MCP_", env_file=".env")

    name: str = "Insurance MCP Server"
    transport: Literal["stdio", "http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    redact_pii: bool = True

settings = Settings()
