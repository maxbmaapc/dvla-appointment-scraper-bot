#!/usr/bin/env python3
"""
DVLA Appointment Scraper Bot
Main entry point for the Telegram bot
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from bot.handlers import setup_handlers
from bot.scraper import DVLAAppointmentScraper
from config.settings import Settings
from utils.helpers import setup_logging

# Load environment variables
load_dotenv()

async def main():
    """Main function to start the bot"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load settings
        settings = Settings()
        
        # Initialize scraper
        scraper = DVLAAppointmentScraper(settings)
        
        # Setup and start bot
        from telegram.ext import Application
        
        # Create application
        application = Application.builder().token(settings.telegram_bot_token).build()
        
        # Setup handlers
        setup_handlers(application, scraper)
        
        logger.info("Starting DVLA Appointment Scraper Bot...")
        
        # Start the bot
        await application.initialize()
        await application.start()
        await application.run_polling(allowed_updates=[])
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())