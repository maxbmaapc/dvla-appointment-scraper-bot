"""
Configuration settings for the DVLA Appointment Scraper Bot
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings loaded from environment variables"""
    
    # Telegram Bot Configuration
    telegram_bot_token: str
    
    # DVLA Credentials
    dvla_username: str
    dvla_password: str
    
    # Database Configuration
    database_url: str = "sqlite:///dvla_bot.db"
    
    # Logging
    log_level: str = "INFO"
    
    # Scraping Configuration
    scrape_interval: int = 300  # seconds
    max_retries: int = 3
    request_timeout: int = 30
    
    # Notification Settings
    notification_cooldown: int = 300  # seconds
    
    def __post_init__(self):
        """Load settings from environment variables"""
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.dvla_username = os.getenv("DVLA_USERNAME", "")
        self.dvla_password = os.getenv("DVLA_PASSWORD", "")
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.scrape_interval = int(os.getenv("SCRAPE_INTERVAL", self.scrape_interval))
        self.max_retries = int(os.getenv("MAX_RETRIES", self.max_retries))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", self.request_timeout))
        self.notification_cooldown = int(os.getenv("NOTIFICATION_COOLDOWN", self.notification_cooldown))
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_fields = [
            self.telegram_bot_token,
            self.dvla_username,
            self.dvla_password
        ]
        
        return all(field for field in required_fields)