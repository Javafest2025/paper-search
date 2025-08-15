"""
Central configuration management for the application.

This module provides a centralized way to load and access environment variables
throughout the application using Pydantic settings.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class automatically loads environment variables from .env file
    and provides type-safe access to configuration values.
    """
    
    # Server Configuration
    app_name: str = Field(default="Paper Search API", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # RabbitMQ Configuration
    rabbitmq_user: str = Field(description="RabbitMQ username")
    rabbitmq_password: str = Field(description="RabbitMQ password")
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_vhost: str = Field(default="/", description="RabbitMQ virtual host")
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Security Configuration
    secret_key: Optional[str] = Field(default=None, description="Secret key for encryption")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")

    # Optional external service credentials (accepted if present)
    core_api_key: Optional[str] = Field(default=None, description="CORE API key")
    unpaywall_email: Optional[str] = Field(default=None, description="Unpaywall contact email")
    b2_key_id: Optional[str] = Field(default=None, description="Backblaze B2 key id")
    b2_application_key: Optional[str] = Field(default=None, description="Backblaze B2 application key")
    b2_bucket_name: Optional[str] = Field(default=None, description="Backblaze B2 bucket name")
    b2_bucket_id: Optional[str] = Field(default=None, description="Backblaze B2 bucket id")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    s2_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API key")

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )
    
    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ connection URL."""
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )
    
    @property
    def is_development(self) -> bool:
        """Check if application is in development mode."""
        return self.log_level.upper() == "DEBUG"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Uses lru_cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    
    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Convenience instance for easy importing
settings = get_settings() 