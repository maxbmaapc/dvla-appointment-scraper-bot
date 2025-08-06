"""
Utility helper functions for the DVLA Appointment Scraper Bot
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if log_file and not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

def format_appointment_message(appointments: List[Dict]) -> str:
    """Format appointment data into a readable message"""
    if not appointments:
        return "No appointments found."
    
    message = "🎉 **Appointments Available!**\n\n"
    
    for i, appointment in enumerate(appointments, 1):
        message += f"**{i}. {appointment.get('center', 'Unknown Center')}**\n"
        message += f"📅 Date: {appointment.get('date', 'Unknown')}\n"
        message += f"🕐 Time: {appointment.get('time', 'Unknown')}\n"
        message += f"🚗 Test Type: {appointment.get('test_type', 'Unknown')}\n"
        
        if appointment.get('url'):
            message += f"🔗 [Book Now]({appointment['url']})\n"
        
        message += "\n"
    
    return message

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate date range format and logic"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Check if start date is before end date
        if start >= end:
            return False
        
        # Check if dates are not too far in the future (e.g., max 6 months)
        max_future = datetime.now() + timedelta(days=180)
        if end > max_future:
            return False
        
        return True
        
    except ValueError:
        return False

def parse_time_preferences(time_str: str) -> List[str]:
    """Parse time preferences from string"""
    if not time_str:
        return []
    
    # Common time formats
    time_mappings = {
        'morning': ['09:00', '10:00', '11:00', '12:00'],
        'afternoon': ['13:00', '14:00', '15:00', '16:00'],
        'evening': ['17:00', '18:00', '19:00'],
        'any': []
    }
    
    times = []
    for time_pref in time_str.lower().split(','):
        time_pref = time_pref.strip()
        if time_pref in time_mappings:
            times.extend(time_mappings[time_pref])
        elif ':' in time_pref:  # Specific time like "14:30"
            times.append(time_pref)
    
    return times

def calculate_next_check_time(interval_minutes: int) -> datetime:
    """Calculate the next check time based on interval"""
    return datetime.now() + timedelta(minutes=interval_minutes)

def format_duration(minutes: int) -> str:
    """Format duration in human-readable format"""
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes < 1440:  # Less than 24 hours
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours {remaining_minutes} minutes"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        if remaining_hours == 0:
            return f"{days} days"
        else:
            return f"{days} days {remaining_hours} hours"

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def validate_center_code(center_code: str) -> bool:
    """Validate DVLA test center code format"""
    if not center_code:
        return False
    
    # Basic validation - center codes are typically alphanumeric
    return center_code.replace('-', '').replace('_', '').isalnum()

def create_inline_keyboard(buttons: List[Dict]) -> Dict:
    """Create inline keyboard markup for Telegram"""
    keyboard = []
    current_row = []
    
    for button in buttons:
        current_row.append({
            'text': button['text'],
            'callback_data': button['callback_data']
        })
        
        if button.get('new_row', False) or len(current_row) >= 2:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row)
    
    return {'inline_keyboard': keyboard}

def parse_callback_data(data: str) -> Dict:
    """Parse callback data from Telegram inline buttons"""
    try:
        parts = data.split('_')
        if len(parts) >= 2:
            return {
                'action': parts[0],
                'params': parts[1:]
            }
        else:
            return {'action': data, 'params': []}
    except Exception:
        return {'action': 'unknown', 'params': []}

def get_emoji_for_status(status: str) -> str:
    """Get appropriate emoji for status"""
    emoji_map = {
        'active': '🟢',
        'inactive': '🔴',
        'pending': '🟡',
        'error': '❌',
        'success': '✅',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    return emoji_map.get(status.lower(), '❓')

def format_statistics(stats: Dict) -> str:
    """Format statistics into readable text"""
    if not stats:
        return "No statistics available."
    
    text = "📊 **Statistics**\n\n"
    
    for key, value in stats.items():
        if isinstance(value, datetime):
            text += f"**{key.title()}:** {value.strftime('%Y-%m-%d %H:%M')}\n"
        elif isinstance(value, (int, float)):
            text += f"**{key.title()}:** {value:,}\n"
        else:
            text += f"**{key.title()}:** {value}\n"
    
    return text

def check_rate_limit(last_check: datetime, min_interval: int = 60) -> bool:
    """Check if enough time has passed since last check"""
    if not last_check:
        return True
    
    time_since_last = datetime.now() - last_check
    return time_since_last.total_seconds() >= min_interval