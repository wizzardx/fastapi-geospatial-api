# File: config.py
# Day 8: Environment configuration

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    """Application configuration"""

    # Environment
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./sensors.db"

    # API
    api_title: str = "Geospatial API"
    api_version: str = "2.0.0"

    # AWS
    aws_region: str = "us-east-1"

    # AI
    ai_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    ai_max_tokens: int = 1000

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load config from environment variables"""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            database_url=os.getenv("DATABASE_URL", "sqlite:///./sensors.db"),
            api_title=os.getenv("API_TITLE", "Geospatial API"),
            api_version=os.getenv("API_VERSION", "2.0.0"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            ai_model=os.getenv("AI_MODEL", "anthropic.claude-3-haiku-20240307-v1:0"),
            ai_max_tokens=int(os.getenv("AI_MAX_TOKENS", "1000"))
        )

# Global config
config = AppConfig.from_env()

# Update main.py to use config
app = FastAPI(
    title=config.api_title,
    description="AI-powered geospatial analytics",
    version=config.api_version,
    debug=config.debug
)
