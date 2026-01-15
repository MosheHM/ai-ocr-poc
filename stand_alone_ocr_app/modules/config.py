"""Environment-based configuration management."""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Literal

logger = logging.getLogger(__name__)

Environment = Literal["development", "production"]


def _load_env_file():
    """Load .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.debug("python-dotenv not installed, skipping .env file loading")


_load_env_file()


def _get_required_env(var_name: str) -> str:
    """Get required environment variable or raise."""
    value = os.environ.get(var_name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{var_name}' is not set.")
    return value


def _get_optional_env(var_name: str, default: str) -> str:
    return os.environ.get(var_name, default)


@dataclass(frozen=True)
class AppConfig:
    """Application configuration (immutable)."""
    environment: Environment
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int


def get_environment() -> Environment:
    return os.environ.get('ENVIRONMENT', 'development').lower()


def get_app_config() -> AppConfig:
    """Get complete application configuration."""
    return AppConfig(
        environment=get_environment(),
        gemini_api_key=_get_required_env('GEMINI_API_KEY'),
        gemini_model=_get_optional_env('GEMINI_MODEL', 'gemini-2.5-flash'),
        gemini_timeout_seconds=int(_get_optional_env('GEMINI_TIMEOUT_SECONDS', '300')),
    )


def is_development() -> bool:
    return get_environment() == 'development'


def is_production() -> bool:
    return get_environment() == 'production'
