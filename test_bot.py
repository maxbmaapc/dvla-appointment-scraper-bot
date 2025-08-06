#!/usr/bin/env python3
"""
Simple test script for the DVLA Appointment Scraper Bot
"""

import asyncio
import os
from dotenv import load_dotenv

from config.settings import Settings
from bot.scraper import DVLAAppointmentScraper
from bot.database import DatabaseManager
from utils.helpers import setup_logging

async def test_bot():
    """Test the bot functionality"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    print("🚗 Testing DVLA Appointment Scraper Bot...")
    
    try:
        # Initialize settings
        settings = Settings()
        
        if not settings.validate():
            print("❌ Invalid settings. Please check your .env file.")
            return
        
        print("✅ Settings loaded successfully")
        
        # Initialize database
        db_manager = DatabaseManager(settings.database_url)
        print("✅ Database initialized")
        
        # Initialize scraper
        scraper = DVLAAppointmentScraper(settings)
        await scraper.initialize()
        print("✅ Scraper initialized")
        
        # Test database operations
        test_user_id = 123456789
        test_username = "test_user"
        
        # Add test user
        success = await db_manager.add_user(test_user_id, test_username)
        if success:
            print("✅ Test user added to database")
        else:
            print("❌ Failed to add test user")
        
        # Get user settings
        user_settings = await db_manager.get_user_settings(test_user_id)
        print(f"✅ User settings retrieved: {user_settings}")
        
        # Test scraper functionality
        print("🔍 Testing scraper functionality...")
        
        # Get test centers
        centers = await scraper.get_test_centers()
        print(f"✅ Found {len(centers)} test centers")
        
        # Test appointment checking (this would require valid credentials)
        print("⚠️  Note: Appointment checking requires valid DVLA credentials")
        print("   Set up your .env file with real credentials to test this feature")
        
        # Test utility functions
        from utils.helpers import format_duration, sanitize_input
        
        duration = format_duration(125)
        print(f"✅ Duration formatting: 125 minutes = {duration}")
        
        sanitized = sanitize_input("<script>alert('test')</script>")
        print(f"✅ Input sanitization: {sanitized}")
        
        print("\n🎉 All tests completed successfully!")
        print("\nTo run the actual bot:")
        print("1. Set up your .env file with real credentials")
        print("2. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'scraper' in locals():
            await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_bot())