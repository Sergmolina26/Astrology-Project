from datetime import datetime, timedelta
from typing import List, Optional
from pymongo import MongoClient
import os

class CalendarBlockingService:
    """Service to handle calendar blocking to prevent double bookings"""
    
    def __init__(self, db):
        self.db = db
    
    async def is_time_slot_available(self, start_time: datetime, end_time: datetime, reader_id: str) -> bool:
        """Check if a time slot is available for booking"""
        # Check for existing confirmed sessions that overlap
        overlapping_sessions = await self.db.sessions.find({
            "reader_id": reader_id,
            "status": {"$in": ["confirmed", "completed"]},
            "$or": [
                # Session starts during our time slot
                {
                    "start_at": {"$gte": start_time, "$lt": end_time}
                },
                # Session ends during our time slot  
                {
                    "end_at": {"$gt": start_time, "$lte": end_time}
                },
                # Session encompasses our time slot
                {
                    "start_at": {"$lte": start_time},
                    "end_at": {"$gte": end_time}
                }
            ]
        }).to_list(None)
        
        return len(overlapping_sessions) == 0
    
    async def get_reader_availability(self, reader_id: str, date: datetime, buffer_minutes: int = 15) -> List[dict]:
        """Get available time slots for a reader on a specific date"""
        # Get all sessions for the day
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        sessions = await self.db.sessions.find({
            "reader_id": reader_id,
            "status": {"$in": ["confirmed", "completed"]},
            "start_at": {"$gte": day_start, "$lt": day_end}
        }).sort("start_at", 1).to_list(None)
        
        # Define business hours (9 AM - 8 PM)
        business_start = day_start.replace(hour=9)
        business_end = day_start.replace(hour=20)
        
        available_slots = []
        current_time = business_start
        
        for session in sessions:
            session_start = session["start_at"]
            session_end = session["end_at"]
            
            # Add buffer time around existing sessions
            buffered_start = session_start - timedelta(minutes=buffer_minutes)
            buffered_end = session_end + timedelta(minutes=buffer_minutes)
            
            # If there's a gap before this session
            if current_time < buffered_start:
                available_slots.append({
                    "start": current_time,
                    "end": buffered_start,
                    "duration_minutes": int((buffered_start - current_time).total_seconds() / 60)
                })
            
            # Move current time past this session
            current_time = max(current_time, buffered_end)
        
        # Add any remaining time until business close
        if current_time < business_end:
            available_slots.append({
                "start": current_time,
                "end": business_end,
                "duration_minutes": int((business_end - current_time).total_seconds() / 60)
            })
        
        return available_slots
    
    async def block_time_slot(self, start_time: datetime, end_time: datetime, reader_id: str, 
                            session_id: str, client_id: str, service_type: str) -> bool:
        """Block a time slot by creating a session"""
        # Double-check availability
        if not await self.is_time_slot_available(start_time, end_time, reader_id):
            return False
            
        # Time slot is available, session will be created by calling code
        return True