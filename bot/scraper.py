"""
DVLA Appointment Scraper
Handles scraping of DVLA appointment availability
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import Settings

logger = logging.getLogger(__name__)

class DVLAAppointmentScraper:
    """Scrapes DVLA appointment availability"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = None
        self.driver = None
        self.is_logged_in = False
        
        # DVLA URLs (these would need to be updated with actual URLs)
        self.base_url = "https://www.gov.uk/book-driving-test"
        self.login_url = "https://www.gov.uk/book-driving-test/sign-in"
        self.appointments_url = "https://www.gov.uk/book-driving-test/appointments"
        
        # Common DVLA test centers (example data)
        self.test_centers = {
            "london": "London Test Center",
            "manchester": "Manchester Test Center", 
            "birmingham": "Birmingham Test Center",
            "leeds": "Leeds Test Center",
            "liverpool": "Liverpool Test Center",
            "sheffield": "Sheffield Test Center",
            "edinburgh": "Edinburgh Test Center",
            "glasgow": "Glasgow Test Center",
            "cardiff": "Cardiff Test Center",
            "bristol": "Bristol Test Center"
        }
    
    async def initialize(self):
        """Initialize the scraper session"""
        try:
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.settings.request_timeout)
            )
            
            # Initialize Selenium driver
            await self._setup_driver()
            
            logger.info("DVLA scraper initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            raise
    
    async def _setup_driver(self):
        """Setup Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Use webdriver-manager to handle driver installation
            driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(driver_path, options=chrome_options)
            
            logger.info("Selenium WebDriver setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            raise
    
    async def login(self) -> bool:
        """Login to DVLA website"""
        try:
            if self.is_logged_in:
                return True
            
            logger.info("Attempting to login to DVLA website...")
            
            # Navigate to login page
            self.driver.get(self.login_url)
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Find and fill username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(self.settings.dvla_username)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.settings.dvla_password)
            
            # Submit login form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(3)
            
            # Check if login was successful
            if "dashboard" in self.driver.current_url or "appointments" in self.driver.current_url:
                self.is_logged_in = True
                logger.info("Successfully logged in to DVLA website")
                return True
            else:
                logger.error("Login failed - redirected to unexpected page")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def check_appointments(self, user_settings: Dict) -> List[Dict]:
        """Check for available appointments based on user settings"""
        try:
            # Ensure we're logged in
            if not await self.login():
                logger.error("Cannot check appointments - not logged in")
                return []
            
            logger.info("Checking for available appointments...")
            
            # Navigate to appointments page
            self.driver.get(self.appointments_url)
            await asyncio.sleep(2)
            
            # Apply user filters
            await self._apply_filters(user_settings)
            
            # Wait for results to load
            await asyncio.sleep(3)
            
            # Parse available appointments
            appointments = await self._parse_appointments()
            
            logger.info(f"Found {len(appointments)} available appointments")
            return appointments
            
        except Exception as e:
            logger.error(f"Error checking appointments: {e}")
            return []
    
    async def _apply_filters(self, user_settings: Dict):
        """Apply user filters to the appointment search"""
        try:
            # Apply location filter
            if 'centers' in user_settings:
                centers = user_settings['centers']
                if isinstance(centers, str):
                    centers = [centers]
                
                for center in centers:
                    # Find and select the center
                    center_element = self.driver.find_element(
                        By.XPATH, f"//input[@value='{center}']"
                    )
                    center_element.click()
                    await asyncio.sleep(1)
            
            # Apply date range filter
            if 'date_range' in user_settings:
                date_range = user_settings['date_range']
                # Implementation would depend on the actual DVLA website structure
                # This is a placeholder for the date selection logic
                pass
            
            # Apply other filters as needed
            # (test type, time preferences, etc.)
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
    
    async def _parse_appointments(self) -> List[Dict]:
        """Parse available appointments from the page"""
        appointments = []
        
        try:
            # Find appointment slots
            appointment_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".appointment-slot"
            )
            
            for element in appointment_elements:
                try:
                    appointment = {
                        'date': element.get_attribute('data-date'),
                        'time': element.get_attribute('data-time'),
                        'center': element.get_attribute('data-center'),
                        'test_type': element.get_attribute('data-test-type'),
                        'url': element.get_attribute('href')
                    }
                    
                    # Validate appointment data
                    if appointment['date'] and appointment['time']:
                        appointments.append(appointment)
                        
                except Exception as e:
                    logger.warning(f"Error parsing appointment element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing appointments: {e}")
        
        return appointments
    
    async def get_test_centers(self) -> Dict[str, str]:
        """Get available test centers"""
        return self.test_centers
    
    async def check_specific_center(self, center_id: str) -> List[Dict]:
        """Check appointments for a specific test center"""
        try:
            user_settings = {'centers': [center_id]}
            return await self.check_appointments(user_settings)
            
        except Exception as e:
            logger.error(f"Error checking center {center_id}: {e}")
            return []
    
    async def monitor_continuously(self, user_settings: Dict, callback):
        """Continuously monitor for appointments and call callback when found"""
        while True:
            try:
                appointments = await self.check_appointments(user_settings)
                
                if appointments:
                    await callback(appointments)
                
                # Wait before next check
                await asyncio.sleep(self.settings.scrape_interval)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.session:
                await self.session.close()
            
            if self.driver:
                self.driver.quit()
                
            logger.info("Scraper resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error closing scraper: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass