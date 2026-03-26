from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration using Pydantic BaseSettings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database Configuration
    POSTGRES_USER: str = "census_user"
    POSTGRES_PASSWORD: str = "census_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "census_db"
    
    # Network Configuration
    LOCAL_SUBNET_PREFIX: str = "10.55."  # For lab safety - only scrape these IPs
    
    # Optional Configuration
    LOG_LEVEL: str = "INFO"
    SCHEDULER_ENABLED: bool = True
    
    @property
    def DATABASE_URL(self) -> str:
        """Async database URL for asyncpg."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync database URL for table initialization."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Application Settings
    APP_NAME: str = "CENSUS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # External Services
    axlerate_base_url: str = "http://axlerate:8000"
    
    # Active Directory Configuration
    ad_server_url: str = "ldap://domain-controller.military.net"
    ad_bind_user: str = "cn=service_account,cn=Users,dc=military,dc=net"
    ad_bind_password: str = "ad_password"
    ad_search_base: str = "DC=military,DC=net"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
