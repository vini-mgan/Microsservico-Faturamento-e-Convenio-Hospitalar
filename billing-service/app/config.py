from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "billing_user"
    MYSQL_PASSWORD: str = "billing_password"
    MYSQL_DATABASE: str = "billing_db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_BILLING_EVENTS: str = "billing.events"
    
    # Service
    SERVICE_NAME: str = "billing-service"
    SERVICE_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # OAuth2/OIDC
    AUTH_ENABLED: str = "false"  # Desabilitado por padrão para desenvolvimento
    OIDC_ISSUER: str = "http://localhost:8080/auth/realms/master"
    OIDC_AUDIENCE: str = "billing-service"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    # TLS/mTLS
    TLS_ENABLED: str = "false"
    TLS_CERT_FILE: Optional[str] = None
    TLS_KEY_FILE: Optional[str] = None
    TLS_CA_FILE: Optional[str] = None
    
    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

