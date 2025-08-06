"""
Database management for DVLA Appointment Scraper Bot
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """User table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    settings = Column(Text)  # JSON string of user settings

class UserSession(Base):
    """User monitoring sessions"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_minutes = Column(Integer)
    checks_performed = Column(Integer, default=0)
    appointments_found = Column(Integer, default=0)

class AppointmentLog(Base):
    """Log of found appointments"""
    __tablename__ = 'appointment_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(Integer)
    appointment_data = Column(Text)  # JSON string of appointment details
    found_at = Column(DateTime, default=datetime.utcnow)
    was_notified = Column(Boolean, default=False)

class MonitoringCheck(Base):
    """Log of monitoring checks"""
    __tablename__ = 'monitoring_checks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(Integer)
    check_time = Column(DateTime, default=datetime.utcnow)
    appointments_found = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

class DatabaseManager:
    """Manages database operations for the bot"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    async def add_user(self, telegram_id: int, username: str) -> bool:
        """Add a new user to the database"""
        try:
            with self.get_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if existing_user:
                    # Update existing user
                    existing_user.username = username
                    existing_user.is_active = True
                    session.commit()
                    logger.info(f"Updated existing user {telegram_id}")
                else:
                    # Create new user
                    new_user = User(
                        telegram_id=telegram_id,
                        username=username,
                        settings=json.dumps({})
                    )
                    session.add(new_user)
                    session.commit()
                    logger.info(f"Added new user {telegram_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding user {telegram_id}: {e}")
            return False
    
    async def get_user_settings(self, telegram_id: int) -> Dict:
        """Get user settings"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user and user.settings:
                    return json.loads(user.settings)
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting user settings for {telegram_id}: {e}")
            return {}
    
    async def update_user_settings(self, telegram_id: int, settings: Dict) -> bool:
        """Update user settings"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Merge with existing settings
                    current_settings = json.loads(user.settings) if user.settings else {}
                    current_settings.update(settings)
                    user.settings = json.dumps(current_settings)
                    session.commit()
                    
                    logger.info(f"Updated settings for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"User {telegram_id} not found for settings update")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating user settings for {telegram_id}: {e}")
            return False
    
    async def log_monitoring_start(self, telegram_id: int) -> Optional[int]:
        """Log the start of a monitoring session"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    session_record = UserSession(
                        user_id=user.id,
                        started_at=datetime.utcnow()
                    )
                    session.add(session_record)
                    session.commit()
                    
                    logger.info(f"Started monitoring session for user {telegram_id}")
                    return session_record.id
                else:
                    logger.warning(f"User {telegram_id} not found for session start")
                    return None
                    
        except Exception as e:
            logger.error(f"Error logging monitoring start for {telegram_id}: {e}")
            return None
    
    async def log_monitoring_stop(self, telegram_id: int) -> bool:
        """Log the end of a monitoring session"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Find active session
                    active_session = session.query(UserSession).filter(
                        UserSession.user_id == user.id,
                        UserSession.ended_at.is_(None)
                    ).first()
                    
                    if active_session:
                        active_session.ended_at = datetime.utcnow()
                        active_session.duration_minutes = int(
                            (active_session.ended_at - active_session.started_at).total_seconds() / 60
                        )
                        session.commit()
                        
                        logger.info(f"Stopped monitoring session for user {telegram_id}")
                        return True
                    else:
                        logger.warning(f"No active session found for user {telegram_id}")
                        return False
                else:
                    logger.warning(f"User {telegram_id} not found for session stop")
                    return False
                    
        except Exception as e:
            logger.error(f"Error logging monitoring stop for {telegram_id}: {e}")
            return False
    
    async def log_appointments_found(self, telegram_id: int, appointments: List[Dict]) -> bool:
        """Log found appointments"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Get current active session
                    active_session = session.query(UserSession).filter(
                        UserSession.user_id == user.id,
                        UserSession.ended_at.is_(None)
                    ).first()
                    
                    for appointment in appointments:
                        appointment_log = AppointmentLog(
                            user_id=user.id,
                            session_id=active_session.id if active_session else None,
                            appointment_data=json.dumps(appointment),
                            found_at=datetime.utcnow()
                        )
                        session.add(appointment_log)
                    
                    # Update session stats
                    if active_session:
                        active_session.appointments_found += len(appointments)
                    
                    session.commit()
                    
                    logger.info(f"Logged {len(appointments)} appointments for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"User {telegram_id} not found for appointment logging")
                    return False
                    
        except Exception as e:
            logger.error(f"Error logging appointments for {telegram_id}: {e}")
            return False
    
    async def log_monitoring_check(self, telegram_id: int, appointments_found: int, success: bool = True, error_message: str = None) -> bool:
        """Log a monitoring check"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Get current active session
                    active_session = session.query(UserSession).filter(
                        UserSession.user_id == user.id,
                        UserSession.ended_at.is_(None)
                    ).first()
                    
                    check_log = MonitoringCheck(
                        user_id=user.id,
                        session_id=active_session.id if active_session else None,
                        check_time=datetime.utcnow(),
                        appointments_found=appointments_found,
                        success=success,
                        error_message=error_message
                    )
                    session.add(check_log)
                    
                    # Update session stats
                    if active_session:
                        active_session.checks_performed += 1
                    
                    session.commit()
                    
                    return True
                else:
                    logger.warning(f"User {telegram_id} not found for check logging")
                    return False
                    
        except Exception as e:
            logger.error(f"Error logging monitoring check for {telegram_id}: {e}")
            return False
    
    async def get_user_stats(self, telegram_id: int) -> Dict:
        """Get comprehensive user statistics"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if not user:
                    return {}
                
                # Get session statistics
                sessions = session.query(UserSession).filter(UserSession.user_id == user.id).all()
                total_sessions = len(sessions)
                total_checks = sum(s.checks_performed for s in sessions)
                total_appointments = sum(s.appointments_found for s in sessions)
                
                # Get last activity
                last_check = session.query(MonitoringCheck).filter(
                    MonitoringCheck.user_id == user.id
                ).order_by(MonitoringCheck.check_time.desc()).first()
                
                last_activity = last_check.check_time if last_check else None
                
                # Get recent activity (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_checks = session.query(MonitoringCheck).filter(
                    MonitoringCheck.user_id == user.id,
                    MonitoringCheck.check_time >= week_ago
                ).count()
                
                return {
                    'sessions': total_sessions,
                    'total_checks': total_checks,
                    'appointments_found': total_appointments,
                    'last_activity': last_activity.isoformat() if last_activity else None,
                    'recent_checks': recent_checks,
                    'recent_activity': f"{recent_checks} checks in the last 7 days"
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats for {telegram_id}: {e}")
            return {}
    
    async def get_global_stats(self) -> Dict:
        """Get global bot statistics"""
        try:
            with self.get_session() as session:
                # Total users
                total_users = session.query(User).filter(User.is_active == True).count()
                
                # Appointments found today
                today = datetime.utcnow().date()
                appointments_today = session.query(AppointmentLog).filter(
                    AppointmentLog.found_at >= today
                ).count()
                
                # Active sessions
                active_sessions = session.query(UserSession).filter(
                    UserSession.ended_at.is_(None)
                ).count()
                
                return {
                    'total_users': total_users,
                    'appointments_today': appointments_today,
                    'active_sessions': active_sessions
                }
                
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent database bloat"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with self.get_session() as session:
                # Clean up old monitoring checks
                old_checks = session.query(MonitoringCheck).filter(
                    MonitoringCheck.check_time < cutoff_date
                ).delete()
                
                # Clean up old appointment logs
                old_appointments = session.query(AppointmentLog).filter(
                    AppointmentLog.found_at < cutoff_date
                ).delete()
                
                session.commit()
                
                logger.info(f"Cleaned up {old_checks} old checks and {old_appointments} old appointments")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")