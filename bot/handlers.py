"""
Telegram bot command handlers for DVLA Appointment Scraper
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.database import DatabaseManager
from bot.scraper import DVLAAppointmentScraper

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handles all Telegram bot commands and interactions"""
    
    def __init__(self, scraper: DVLAAppointmentScraper, db_manager: DatabaseManager):
        self.scraper = scraper
        self.db_manager = db_manager
        self.active_monitors = {}  # user_id -> monitoring_task
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        welcome_message = f"""
🚗 Welcome to DVLA Appointment Scraper Bot, {user_name}!

This bot helps you monitor DVLA appointments and get notified when slots become available.

📋 Available commands:
/start - Show this welcome message
/help - Show detailed help
/settings - Configure your preferences
/monitor - Start monitoring appointments
/status - Check monitoring status
/stop - Stop monitoring
/stats - View appointment statistics

To get started, use /settings to configure your preferences, then /monitor to begin tracking appointments.
        """
        
        await update.message.reply_text(welcome_message)
        
        # Register user in database
        await self.db_manager.add_user(user_id, user_name)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🔍 **DVLA Appointment Scraper Bot Help**

**Commands:**
• `/start` - Initialize the bot
• `/help` - Show this help message
• `/settings` - Configure monitoring preferences
• `/monitor` - Start monitoring appointments
• `/status` - Check current monitoring status
• `/stop` - Stop monitoring
• `/stats` - View appointment statistics

**How it works:**
1. Use `/settings` to configure your preferences:
   - Preferred DVLA centers
   - Date range
   - Notification frequency
2. Use `/monitor` to start tracking
3. Get instant notifications when appointments become available
4. Use `/stop` when you're done

**Features:**
• Real-time monitoring of DVLA appointment availability
• Instant Telegram notifications
• Filter by location and date
• Automatic retry on failures
• Statistics and tracking

For support, contact the bot administrator.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        
        # Get current user settings
        user_settings = await self.db_manager.get_user_settings(user_id)
        
        # Create settings keyboard
        keyboard = [
            [InlineKeyboardButton("📍 Set Preferred Centers", callback_data="settings_centers")],
            [InlineKeyboardButton("📅 Set Date Range", callback_data="settings_dates")],
            [InlineKeyboardButton("🔔 Notification Settings", callback_data="settings_notifications")],
            [InlineKeyboardButton("⚙️ Advanced Settings", callback_data="settings_advanced")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = f"""
⚙️ **Your Settings**

**Preferred Centers:** {user_settings.get('centers', 'Not set')}
**Date Range:** {user_settings.get('date_range', 'Not set')}
**Notifications:** {user_settings.get('notifications', 'Enabled')}

Use the buttons below to configure your preferences:
        """
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monitor command"""
        user_id = update.effective_user.id
        
        # Check if user is already monitoring
        if user_id in self.active_monitors:
            await update.message.reply_text("⚠️ You are already monitoring appointments. Use /stop to stop first.")
            return
        
        # Check if user has configured settings
        user_settings = await self.db_manager.get_user_settings(user_id)
        if not user_settings.get('centers'):
            await update.message.reply_text(
                "❌ Please configure your settings first using /settings"
            )
            return
        
        # Start monitoring
        try:
            # Create monitoring task
            monitoring_task = asyncio.create_task(
                self._monitor_appointments(user_id, user_settings)
            )
            self.active_monitors[user_id] = monitoring_task
            
            await update.message.reply_text(
                "✅ Monitoring started! You'll receive notifications when appointments become available."
            )
            
            # Log monitoring start
            await self.db_manager.log_monitoring_start(user_id)
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for user {user_id}: {e}")
            await update.message.reply_text("❌ Failed to start monitoring. Please try again.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        # Check monitoring status
        is_monitoring = user_id in self.active_monitors
        
        # Get user settings
        user_settings = await self.db_manager.get_user_settings(user_id)
        
        # Get monitoring statistics
        stats = await self.db_manager.get_user_stats(user_id)
        
        status_text = f"""
📊 **Monitoring Status**

**Status:** {'🟢 Active' if is_monitoring else '🔴 Inactive'}
**Preferred Centers:** {user_settings.get('centers', 'Not set')}
**Date Range:** {user_settings.get('date_range', 'Not set')}

**Statistics:**
• Total checks: {stats.get('total_checks', 0)}
• Appointments found: {stats.get('appointments_found', 0)}
• Last check: {stats.get('last_check', 'Never')}

Use /monitor to start or /stop to stop monitoring.
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        if user_id in self.active_monitors:
            # Cancel monitoring task
            self.active_monitors[user_id].cancel()
            del self.active_monitors[user_id]
            
            await update.message.reply_text("🛑 Monitoring stopped.")
            
            # Log monitoring stop
            await self.db_manager.log_monitoring_stop(user_id)
        else:
            await update.message.reply_text("ℹ️ You are not currently monitoring appointments.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        # Get comprehensive statistics
        stats = await self.db_manager.get_user_stats(user_id)
        global_stats = await self.db_manager.get_global_stats()
        
        stats_text = f"""
📈 **Statistics Report**

**Your Activity:**
• Total monitoring sessions: {stats.get('sessions', 0)}
• Total checks performed: {stats.get('total_checks', 0)}
• Appointments found: {stats.get('appointments_found', 0)}
• Last activity: {stats.get('last_activity', 'Never')}

**Global Statistics:**
• Total users: {global_stats.get('total_users', 0)}
• Active monitors: {len(self.active_monitors)}
• Total appointments found today: {global_stats.get('appointments_today', 0)}

**Recent Activity:**
{stats.get('recent_activity', 'No recent activity')}
        """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def _monitor_appointments(self, user_id: int, user_settings: dict):
        """Background task to monitor appointments"""
        while True:
            try:
                # Check for appointments
                appointments = await self.scraper.check_appointments(user_settings)
                
                if appointments:
                    # Send notification
                    await self._send_appointment_notification(user_id, appointments)
                    
                    # Log found appointments
                    await self.db_manager.log_appointments_found(user_id, appointments)
                
                # Wait before next check
                await asyncio.sleep(self.scraper.settings.scrape_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Monitoring cancelled for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for user {user_id}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _send_appointment_notification(self, user_id: int, appointments: list):
        """Send appointment notification to user"""
        try:
            # This would use the bot context to send messages
            # For now, we'll just log it
            logger.info(f"Appointments found for user {user_id}: {appointments}")
            
            # In a real implementation, you would send a message like:
            # await context.bot.send_message(
            #     chat_id=user_id,
            #     text=f"🎉 Appointments available!\n{appointments}"
            # )
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

def setup_handlers(application, scraper: DVLAAppointmentScraper, db_manager: DatabaseManager):
    """Setup all bot handlers"""
    handlers = BotHandlers(scraper, db_manager)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("settings", handlers.settings_command))
    application.add_handler(CommandHandler("monitor", handlers.monitor_command))
    application.add_handler(CommandHandler("status", handlers.status_command))
    application.add_handler(CommandHandler("stop", handlers.stop_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    
    # Add callback query handlers for settings
    application.add_handler(CallbackQueryHandler(handlers._handle_callback))
    
    return handlers

# Import asyncio for the monitoring task
import asyncio