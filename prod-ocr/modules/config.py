"""Environment-based configuration management."""
import os
import logging
from typing import Optional, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

Environment = Literal["development", "production"]


@dataclass
class StorageConfig:
    """Azure Blob Storage configuration."""
    account_name: str
    access_key: str
    input_container: str
    results_container: str
    connection_string: Optional[str] = None


@dataclass
class QueueStorageConfig:
    """Azure Queue Storage configuration."""
    account_name: str
    access_key: str
    tasks_queue: str
    results_queue: str
    connection_string: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration."""
    environment: Environment
    storage: StorageConfig
    queue_storage: QueueStorageConfig
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: int


def get_environment() -> Environment:
    """Get current environment from environment variable.

    Returns:
        Current environment (development or production)

    Raises:
        ValueError: If ENVIRONMENT is not set or invalid
    """
    env = os.getenv('ENVIRONMENT')
    env = env.lower() if env else 'development'

    if env not in ('development', 'production'):
        logger.warning(
            f"Invalid ENVIRONMENT value '{env}', defaulting to 'development'. "
            f"Valid values: development, production"
        )
        return 'development'

    return env


def get_storage_config(environment: Optional[Environment] = None) -> StorageConfig:
    """Get storage configuration for the specified environment.

    Args:
        environment: Target environment (defaults to current environment)

    Returns:
        Storage configuration for the environment

    Raises:
        ValueError: If required configuration is missing
    """
    if environment is None:
        environment = get_environment()

    logger.info(f"Loading storage configuration for environment: {environment}")

    if environment == 'development':
        account_name = os.getenv('DEV_AZURE_STORAGE_ACCOUNT_NAME')
        access_key = os.getenv('DEV_AZURE_STORAGE_ACCESS_KEY')
        connection_string = os.getenv('DEV_AZURE_STORAGE_CONNECTION_STRING')
        input_container = os.getenv('DEV_INPUT_CONTAINER')
        results_container = os.getenv('DEV_RESULTS_CONTAINER')
    else:
        account_name = os.getenv('PROD_AZURE_STORAGE_ACCOUNT_NAME')
        access_key = os.getenv('PROD_AZURE_STORAGE_ACCESS_KEY')
        connection_string = os.getenv('PROD_AZURE_STORAGE_CONNECTION_STRING')
        input_container = os.getenv('PROD_INPUT_CONTAINER')
        results_container = os.getenv('PROD_RESULTS_CONTAINER')
    override_input_container = os.getenv('INPUT_CONTAINER')
    if override_input_container:
        input_container = override_input_container
    override_results_container = os.getenv('RESULTS_CONTAINER')
    if override_results_container:
        results_container = override_results_container

    if not account_name or not access_key:
        raise ValueError(
            f"Missing required storage configuration for {environment} environment. "
            f"Required: AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCESS_KEY "
            f"or {environment.upper()}_AZURE_STORAGE_ACCOUNT_NAME and "
            f"{environment.upper()}_AZURE_STORAGE_ACCESS_KEY"
        )

    config = StorageConfig(
        account_name=account_name,
        access_key=access_key,
        input_container=input_container,
        results_container=results_container,
        connection_string=connection_string
    )

    logger.info(
        f"Storage config loaded: account={account_name}, "
        f"input_container={input_container}, "
        f"results_container={results_container}"
    )

    return config


def get_queue_storage_config(environment: Optional[Environment] = None) -> QueueStorageConfig:
    """Get queue storage configuration for the specified environment.

    Args:
        environment: Target environment (defaults to current environment)

    Returns:
        Queue storage configuration for the environment

    Raises:
        ValueError: If required configuration is missing
    """
    if environment is None:
        environment = get_environment()

    logger.info(f"Loading queue storage configuration for environment: {environment}")

    if environment == 'development':
        # For development, check if separate queue storage is configured
        # Otherwise use same as blob storage (Azurite)
        account_name = os.getenv('DEV_QUEUE_STORAGE_ACCOUNT_NAME')

        access_key = os.getenv('DEV_QUEUE_STORAGE_ACCESS_KEY')
        connection_string = os.getenv('DEV_QUEUE_STORAGE_CONNECTION_STRING')
        tasks_queue = os.getenv('DEV_TASKS_QUEUE')
        results_queue = os.getenv('DEV_RESULTS_QUEUE')
    else:  # production
        # For production, check if separate queue storage is configured
        # Otherwise use same as blob storage
        account_name = (
            os.getenv('PROD_QUEUE_STORAGE_ACCOUNT_NAME')
        )
        access_key = (
            os.getenv('PROD_QUEUE_STORAGE_ACCESS_KEY')
        )
        connection_string = os.getenv('PROD_QUEUE_STORAGE_CONNECTION_STRING')
        tasks_queue = os.getenv('PROD_TASKS_QUEUE')
        results_queue = os.getenv('PROD_RESULTS_QUEUE')

    override_tasks_queue = os.getenv('TASKS_QUEUE')
    if override_tasks_queue:
        tasks_queue = override_tasks_queue
    override_results_queue = os.getenv('RESULTS_QUEUE')
    if override_results_queue:
        results_queue = override_results_queue

    if not account_name or not access_key:
        raise ValueError(
            f"Missing required queue storage configuration for {environment} environment. "
            f"Required: QUEUE_STORAGE_ACCOUNT_NAME and QUEUE_STORAGE_ACCESS_KEY "
            f"or {environment.upper()}_QUEUE_STORAGE_ACCOUNT_NAME and "
            f"{environment.upper()}_QUEUE_STORAGE_ACCESS_KEY"
        )

    config = QueueStorageConfig(
        account_name=account_name,
        access_key=access_key,
        connection_string=connection_string,
        tasks_queue=tasks_queue,
        results_queue=results_queue
    )

    logger.info(
        f"Queue storage config loaded: account={account_name}, "
        f"tasks_queue={tasks_queue}, results_queue={results_queue}"
    )

    return config


def get_app_config(environment: Optional[Environment] = None) -> AppConfig:
    """Get complete application configuration.

    Args:
        environment: Target environment (defaults to current environment)

    Returns:
        Complete application configuration

    Raises:
        ValueError: If required configuration is missing
    """
    if environment is None:
        environment = get_environment()

    storage_config = get_storage_config(environment)
    queue_storage_config = get_queue_storage_config(environment)

    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    gemini_timeout = int(os.getenv('GEMINI_TIMEOUT_SECONDS'))
    return AppConfig(
        environment=environment,
        storage=storage_config,
        queue_storage=queue_storage_config,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_timeout_seconds=gemini_timeout
    )


def is_development() -> bool:
    """Check if running in development environment.

    Returns:
        True if in development environment
    """
    return get_environment() == 'development'


def is_production() -> bool:
    """Check if running in production environment.

    Returns:
        True if in production environment
    """
    return get_environment() == 'production'
