from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str  # Stripe checkout session ID
    payment_id: str  # Our internal payment ID
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    amount: float
    currency: str = "USD"
    payment_status: str = "pending"  # pending, paid, failed, expired
    service_type: Optional[str] = None
    celestia_session_id: Optional[str] = None  # Link to our session booking
    metadata: Optional[Dict[str, str]] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentCreateRequest(BaseModel):
    service_type: str
    session_id: str  # Our Celestia session ID
    origin_url: str

class PaymentStatusResponse(BaseModel):
    payment_status: str
    session_id: str
    amount: float
    currency: str
    service_type: Optional[str] = None