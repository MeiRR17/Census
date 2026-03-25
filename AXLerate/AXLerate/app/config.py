from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Configuration settings for CUCM AXL Gateway
    
    # CUCM Connection Settings
    cucm_ip: str
    axl_user: str
    axl_password: str
    wsdl_path: str
    
    # Optional Settings
    cucm_port: int = 8443
    timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
