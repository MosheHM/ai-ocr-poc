"""Environment-based configuration management."""
import os
import logging
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

Environment = Literal["development", "production"]


def _load_env_file():
    """Load .env file in development only. Production uses Azure App Settings."""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        logger.info("Production environment: using Azure-injected configuration")
        return
    
    try:
        from dotenv import load_dotenv

        base_env = Path(__file__).parent.parent / '.env'
        if base_env.exists():
            load_dotenv(base_env, override=False)

        env_file = Path(__file__).parent.parent / f'.env.{env}'
        if env_file.exists():
            load_dotenv(env_file, override=True)
            logger.info(f"Loaded environment configuration from: {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
    except ImportError:
        logger.debug("python-dotenv not installed, skipping .env file loading")


_load_env_file()


def _get_required_env(var_name: str) -> str:
    """Get required environment variable or raise with clear message."""
    value = os.environ.get(var_name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{var_name}' is not set. "
            f"In production, configure via Azure App Settings with Key Vault reference."
        )
    return value


def _get_optional_env(var_name: str, default: str) -> str:
    """Get optional environment variable with default."""
    return os.environ.get(var_name, default)


@dataclass(frozen=True)
class StorageConfig:
    """Azure Blob Storage configuration (immutable)."""
    account_name: str
    access_key: str
    input_container: str
    results_container: str
    connection_string: Optional[str] = None


@dataclass(frozen=True)
class QueueStorageConfig:
    """Azure Queue Storage configuration (immutable)."""
    account_name: str
    access_key: str
    tasks_queue: str
    results_queue: str
    connection_string: Optional[str] = None


@dataclass(frozen=True)
class AppConfig:
    """Application configuration (immutable)."""
    environment: Environment
    storage: StorageConfig
    queue_storage: QueueStorageConfig
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int


def get_environment() -> Environment:
    """Get current environment from environment variable."""
    env = os.environ.get('ENVIRONMENT', 'development').lower()

    if env not in ('development', 'production'):
        logger.warning(
            f"Invalid ENVIRONMENT value '{env}', defaulting to 'development'."
        )
        return 'development'

    return env


def get_storage_config(environment: Optional[Environment] = None) -> StorageConfig:
    """Get storage configuration for the specified environment."""
    if environment is None:
        environment = get_environment()

    logger.info(f"Loading storage configuration for environment: {environment}")

    config = StorageConfig(
        account_name=_get_required_env('AZURE_STORAGE_ACCOUNT_NAME'),
        access_key=_get_required_env('AZURE_STORAGE_ACCESS_KEY'),
        input_container=_get_required_env('INPUT_CONTAINER'),
        results_container=_get_required_env('RESULTS_CONTAINER'),
        connection_string=os.environ.get('AZURE_STORAGE_CONNECTION_STRING'),
    )

    logger.info(
        f"Storage config loaded: account={config.account_name}, "
        f"input_container={config.input_container}, "
        f"results_container={config.results_container}"
    )

    return config


def get_queue_storage_config(environment: Optional[Environment] = None) -> QueueStorageConfig:
    """Get queue storage configuration for the specified environment."""
    if environment is None:
        environment = get_environment()

    logger.info(f"Loading queue storage configuration for environment: {environment}")

    account_name = (
        os.environ.get('QUEUE_STORAGE_ACCOUNT_NAME') 
        or _get_required_env('AZURE_STORAGE_ACCOUNT_NAME')
    )
    access_key = (
        os.environ.get('QUEUE_STORAGE_ACCESS_KEY') 
        or _get_required_env('AZURE_STORAGE_ACCESS_KEY')
    )
    connection_string = (
        os.environ.get('QUEUE_STORAGE_CONNECTION_STRING') 
        or os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    )

    config = QueueStorageConfig(
        account_name=account_name,
        access_key=access_key,
        tasks_queue=_get_required_env('TASKS_QUEUE'),
        results_queue=_get_required_env('RESULTS_QUEUE'),
        connection_string=connection_string,
    )

    logger.info(
        f"Queue storage config loaded: account={config.account_name}, "
        f"tasks_queue={config.tasks_queue}, results_queue={config.results_queue}"
    )

    return config


def get_app_config(environment: Optional[Environment] = None) -> AppConfig:
    """Get complete application configuration."""
    if environment is None:
        environment = get_environment()

    return AppConfig(
        environment=environment,
        storage=get_storage_config(environment),
        queue_storage=get_queue_storage_config(environment),
        gemini_api_key=_get_required_env('GEMINI_API_KEY'),
        gemini_model=_get_optional_env('GEMINI_MODEL', 'gemini-2.5-flash'),
        gemini_timeout_seconds=int(_get_optional_env('GEMINI_TIMEOUT_SECONDS', '300')),
    )


def is_development() -> bool:
    return get_environment() == 'development'


def is_production() -> bool:
    return get_environment() == 'production'