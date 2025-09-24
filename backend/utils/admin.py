from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class AdminProfileService:
    """Service to handle admin/reader profile management"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_reader_profile(self, user_id: str, profile_data: dict) -> dict:
        """Create or update reader profile with additional business info"""
        
        profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "business_name": profile_data.get("business_name", "Celestia Astrology & Tarot"),
            "bio": profile_data.get("bio", "Professional astrology and tarot reader"),
            "specialties": profile_data.get("specialties", ["Astrology", "Tarot", "Spiritual Guidance"]),
            "experience_years": profile_data.get("experience_years", 5),
            "hourly_rate": profile_data.get("hourly_rate", 120.0),
            "calendar_sync_enabled": profile_data.get("calendar_sync_enabled", False),
            "google_calendar_id": profile_data.get("google_calendar_id"),
            "notification_email": profile_data.get("notification_email"),
            "availability_schedule": profile_data.get("availability_schedule", {
                "monday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "tuesday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "wednesday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "thursday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "friday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "saturday": {"enabled": True, "start": "10:00", "end": "18:00"},
                "sunday": {"enabled": False, "start": "12:00", "end": "17:00"}
            }),
            "services": profile_data.get("services", {
                "tarot-reading": {"name": "Tarot Reading", "price": 85.0, "duration": 60},
                "birth-chart-reading": {"name": "Birth Chart Reading", "price": 120.0, "duration": 90},
                "chart-tarot-combo": {"name": "Chart + Tarot Combo", "price": 165.0, "duration": 120},
                "follow-up": {"name": "Follow-up Session", "price": 45.0, "duration": 30}
            }),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Check if profile already exists
        existing_profile = await self.db.reader_profiles.find_one({"user_id": user_id})
        if existing_profile:
            # Update existing profile
            profile["id"] = existing_profile["id"]
            profile["created_at"] = existing_profile["created_at"]
            await self.db.reader_profiles.update_one(
                {"user_id": user_id},
                {"$set": profile}
            )
        else:
            # Create new profile
            await self.db.reader_profiles.insert_one(profile)
        
        return profile
    
    async def get_reader_profile(self, user_id: str) -> Optional[dict]:
        """Get reader profile by user ID"""
        return await self.db.reader_profiles.find_one({"user_id": user_id})
    
    async def update_notification_settings(self, user_id: str, notification_email: str, 
                                         calendar_sync: bool = False, calendar_id: str = None) -> bool:
        """Update reader notification and calendar settings"""
        update_data = {
            "notification_email": notification_email,
            "calendar_sync_enabled": calendar_sync,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if calendar_id:
            update_data["google_calendar_id"] = calendar_id
        
        result = await self.db.reader_profiles.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def get_reader_notification_email(self, reader_id: str) -> Optional[str]:
        """Get the notification email for a reader"""
        profile = await self.db.reader_profiles.find_one({"user_id": reader_id})
        if profile and profile.get("notification_email"):
            return profile["notification_email"]
        
        # Fallback to user's main email
        user = await self.db.users.find_one({"id": reader_id})
        return user["email"] if user else None