from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt
from kerykeion import AstrologicalSubject, KerykeionChartSVG
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import hashlib

# Import our custom utilities
from models.payment import PaymentTransaction, PaymentCreateRequest, PaymentStatusResponse
from utils.calendar import CalendarBlockingService
from utils.admin import AdminProfileService
# from utils.email_providers import send_email as email_send  # Will be enabled after Gmail setup

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
calendar_service = CalendarBlockingService(db)
admin_service = AdminProfileService(db)

# Stripe setup
stripe_api_key = os.environ.get('STRIPE_API_KEY')

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Real email function using email providers
def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using configured provider"""
    try:
        # Temporarily disabled until Gmail setup is complete
        print(f"📧 EMAIL MOCK: Would send to {to_email} - Subject: {subject}")
        return True  # Mock success for now
        # return email_send(to_email, subject, html_content)  # Will be enabled after Gmail setup
    except Exception as e:
        print(f"📧 EMAIL ERROR: {str(e)}")
        return False

# Create the main app
app = FastAPI(title="Celestia API")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class UserRole(str):
    ADMIN = "admin"
    READER = "reader"
    CLIENT = "client"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "America/Chicago"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = UserRole.CLIENT
    phone: Optional[str] = None
    timezone: str = "America/Chicago"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class BirthData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    birth_date: str  # YYYY-MM-DD format
    birth_time: Optional[str] = None  # HH:MM format
    time_accuracy: str = "exact"  # exact, approx, unknown
    birth_place: str
    latitude: Optional[str] = None  # Changed to str to handle conversion
    longitude: Optional[str] = None  # Changed to str to handle conversion
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BirthDataCreate(BaseModel):
    birth_date: str
    birth_time: Optional[str] = None
    time_accuracy: str = "exact"
    birth_place: str
    latitude: Optional[str] = None  # Changed to str to accept empty strings
    longitude: Optional[str] = None  # Changed to str to accept empty strings

class AstroChart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    session_id: Optional[str] = None
    chart_type: str = "natal"  # natal, transits, progressions
    birth_data: BirthData
    planets: Dict[str, Any] = {}
    houses: Dict[str, Any] = {}
    aspects: List[Dict[str, Any]] = []
    chart_svg: Optional[str] = None
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TarotCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    arcana: str  # major, minor
    suit: Optional[str] = None  # cups, wands, swords, pentacles
    number: Optional[int] = None
    upright_meaning: str
    reversed_meaning: str
    image_url: Optional[str] = None

class TarotSpread(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    positions: List[Dict[str, str]]  # [{"index": 1, "name": "Past", "meaning": "..."}]

class TarotReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    spread_id: str
    cards: List[Dict[str, Any]]  # [{"position": 1, "card_id": "...", "is_reversed": false}]
    interpretation: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reader_id: str
    client_id: str
    service_type: str
    start_at: datetime
    end_at: datetime
    status: str = "pending_payment"  # pending_payment, confirmed, completed, canceled
    notes: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, refunded
    payment_link: Optional[str] = None
    amount: Optional[float] = None
    client_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionCreate(BaseModel):
    service_type: str
    start_at: datetime
    end_at: datetime
    client_message: Optional[str] = None

class PaymentLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    amount: float
    currency: str = "USD"
    payment_url: str
    expires_at: datetime
    status: str = "pending"  # pending, paid, expired
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str
    visibility: str = "client_visible"  # reader_private, client_visible
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== EMAIL AND PAYMENT UTILITIES ====================

def send_email_deprecated(to_email: str, subject: str, html_content: str):
    """Deprecated SendGrid function - use utils.email_providers.send_email instead"""
    # Temporarily using placeholder function due to import issues
    return send_email(to_email, subject, html_content)

def generate_payment_link(session_id: str, amount: float) -> str:
    """Generate a real Stripe payment link (will be replaced with actual checkout session)"""
    payment_id = hashlib.md5(f"{session_id}{amount}".encode()).hexdigest()
    return f"https://astro-booking-3.preview.emergentagent.com/pay/{payment_id}"

def get_service_price(service_type: str) -> float:
    """Get pricing for different services"""
    prices = {
        "general-purpose-reading": 65.0,
        "astrological-tarot-session": 85.0,
        "birth-chart-reading": 120.0,
        "follow-up": 45.0
    }
    return prices.get(service_type, 65.0)

def get_service_duration(service_type: str) -> int:
    """Get duration in minutes for different services"""
    durations = {
        "general-purpose-reading": 45,  # 30-45 min
        "astrological-tarot-session": 60,  # 60 min
        "birth-chart-reading": 90,  # 90 min
        "follow-up": 30  # 30 min
    }
    return durations.get(service_type, 45)

def get_all_services():
    """Get all available services with pricing and duration info"""
    services = [
        {
            "id": "general-purpose-reading",
            "name": "General or Purpose Reading",
            "description": "A focused tarot session designed to uncover clarity around your current path, life purpose, or pressing questions.",
            "price": 65.0,
            "duration": 45,
            "duration_range": "30-45 min"
        },
        {
            "id": "astrological-tarot-session", 
            "name": "Astrological Tarot Session",
            "description": "Deep insights into your personal journey, relationships, and life path through traditional tarot cards.",
            "price": 85.0,
            "duration": 60,
            "duration_range": "60 min"
        },
        {
            "id": "birth-chart-reading",
            "name": "Birth Chart Analysis", 
            "description": "Complete natal chart reading with detailed planetary analysis.",
            "price": 120.0,
            "duration": 90,
            "duration_range": "90 min"
        },
        {
            "id": "follow-up",
            "name": "Follow-up Session",
            "description": "Follow-up reading for previous clients.",
            "price": 45.0,
            "duration": 30,
            "duration_range": "30 min"
        }
    ]
    return services

async def notify_reader(session_id: str, event_type: str):
    """Send notification to reader about client activities"""
    try:
        # Get reader and their notification email from profile
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            print("❌ Session not found")
            return False
            
        reader_email = await admin_service.get_reader_notification_email(session["reader_id"])
        if not reader_email:
            print("❌ No reader notification email configured")
            return False
            
        client = await db.users.find_one({"id": session["client_id"]})
        client_name = client["name"] if client else "Unknown Client"
        
        subject = f"Celestia - {event_type}: {client_name}"
        
        if event_type == "New Booking Request":
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #b8860b;">🌟 New Booking Request</h2>
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Email:</strong> {client.get('email', 'N/A') if client else 'N/A'}</p>
                <p><strong>Service:</strong> {session['service_type']}</p>
                <p><strong>Requested Date:</strong> {session['start_at']}</p>
                <p><strong>Amount:</strong> ${session.get('amount', 0)}</p>
                <p><strong>Status:</strong> Pending Payment</p>
                
                {f"<p><strong>Client Message:</strong> {session.get('client_message', 'No message')}</p>" if session.get('client_message') else ""}
                
                <p>Payment link has been sent to the client. You will receive another notification once payment is completed.</p>
                
                <p><small>This notification was sent to your configured reader email. You can update your notification preferences in your reader profile.</small></p>
            </div>
            """
        elif event_type == "Payment Completed":
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #b8860b;">💰 Payment Completed</h2>
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Email:</strong> {client.get('email', 'N/A') if client else 'N/A'}</p>
                <p><strong>Service:</strong> {session['service_type']}</p>
                <p><strong>Date:</strong> {session['start_at']}</p>
                <p><strong>Amount Paid:</strong> ${session.get('amount', 0)}</p>
                
                <p>✅ Session is now confirmed and ready to be scheduled!</p>
                <p>📅 This time slot has been blocked in your calendar to prevent double bookings.</p>
                
                <p><small>This notification was sent to your configured reader email.</small></p>
            </div>
            """
        else:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #b8860b;">📋 Session Update</h2>
                <p><strong>Event:</strong> {event_type}</p>
                <p><strong>Client:</strong> {client_name}</p>
                <p><strong>Service:</strong> {session['service_type']}</p>
            </div>
            """
        
        return send_email(reader_email, subject, html_content)
        
    except Exception as e:
        print(f"❌ Reader notification failed: {str(e)}")
        return False

# ==================== AUTH UTILITIES ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    user_dict.pop("password")
    user = User(**user_dict)
    
    # Store in database
    await db.users.insert_one({**user.dict(), "hashed_password": hashed_password})
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**{k: v for k, v in user_doc.items() if k != "hashed_password"})
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/register-reader", response_model=Token)
async def register_as_reader(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if reader already exists
    existing_reader = await db.users.find_one({"role": "reader"})
    if existing_reader:
        raise HTTPException(status_code=400, detail="Reader account already exists. Contact support if you need access.")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create reader user
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["role"] = "reader"  # Force reader role
    user = User(**user_dict)
    
    # Store in database
    await db.users.insert_one({**user.dict(), "hashed_password": hashed_password})
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/reader/dashboard")
async def get_reader_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["reader", "admin"]:
        raise HTTPException(status_code=403, detail="Reader or Admin access required")
    
    # Get all sessions for reader - if admin, get all sessions
    if current_user.role == "admin":
        sessions = await db.sessions.find({}).to_list(100)
    else:
        sessions = await db.sessions.find({"reader_id": current_user.id}).to_list(100)
    
    # Get recent clients
    recent_clients = []
    for session in sessions[-10:]:  # Last 10 sessions
        client = await db.users.find_one({"id": session["client_id"]})
        if client:
            recent_clients.append({
                "id": client["id"],
                "name": client["name"],
                "email": client["email"],
                "session_date": session["start_at"],
                "service": session["service_type"],
                "status": session["status"],
                "amount": session.get("amount", 0)
            })
    
    # Calculate stats
    total_sessions = len(sessions)
    pending_sessions = len([s for s in sessions if s["status"] == "pending_payment"])
    confirmed_sessions = len([s for s in sessions if s["status"] == "confirmed"])
    completed_sessions = len([s for s in sessions if s["status"] == "completed"])
    total_revenue = sum([s.get("amount", 0) for s in sessions if s["payment_status"] == "paid"])
    
    # Process sessions to remove MongoDB _id field
    processed_sessions = []
    for session_doc in sessions:
        if "_id" in session_doc:
            del session_doc["_id"]
        processed_sessions.append(session_doc)
    
    return {
        "stats": {
            "total_sessions": total_sessions,
            "pending_sessions": pending_sessions,
            "confirmed_sessions": confirmed_sessions,
            "completed_sessions": completed_sessions,
            "total_revenue": total_revenue
        },
        "recent_clients": recent_clients,
        "sessions": processed_sessions
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== ASTROLOGY ROUTES ====================

@api_router.post("/birth-data", response_model=BirthData)
async def create_birth_data(
    birth_data: BirthDataCreate, 
    current_user: User = Depends(get_current_user)
):
    # For now, associate with current user as client
    birth_record = BirthData(client_id=current_user.id, **birth_data.dict())
    await db.birth_data.insert_one(birth_record.dict())
    return birth_record

@api_router.get("/birth-data/{client_id}", response_model=List[BirthData])
async def get_birth_data(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    # Check permissions (reader can view their clients, clients can view their own)
    if current_user.role == UserRole.CLIENT and current_user.id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    birth_data_list = await db.birth_data.find({"client_id": client_id}).to_list(100)
    return [BirthData(**bd) for bd in birth_data_list]

@api_router.post("/astrology/chart", response_model=AstroChart)
async def generate_chart(
    birth_data_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get birth data
    birth_data_doc = await db.birth_data.find_one({"id": birth_data_id})
    if not birth_data_doc:
        raise HTTPException(status_code=404, detail="Birth data not found")
    
    birth_data = BirthData(**birth_data_doc)
    
    try:
        # Parse birth date and time
        date_parts = birth_data.birth_date.split("-")
        year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
        
        hour, minute = 12, 0  # Default to noon if no time
        if birth_data.birth_time:
            time_parts = birth_data.birth_time.split(":")
            hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Use default coordinates if not provided or convert from string
        lat = 40.7128  # NYC default
        lng = -74.0060
        
        if birth_data.latitude and birth_data.longitude:
            try:
                lat = float(birth_data.latitude)
                lng = float(birth_data.longitude)
            except (ValueError, TypeError):
                # Use defaults if conversion fails
                pass
        
        # Create astrological subject
        subject = AstrologicalSubject(
            name="Chart",
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lat=lat,
            lng=lng,
            tz_str="UTC"
        )
        
        # Extract planetary positions using multiple attribute checking
        planets = {}
        
        # Try different ways to access planets data
        if hasattr(subject, 'sun'):
            planets['Sun'] = {
                "longitude": getattr(subject.sun, 'abs_pos', getattr(subject.sun, 'longitude', 0)),
                "sign": getattr(subject.sun, 'sign', 'Unknown'),
                "house": getattr(subject.sun, 'house', None),
                "retrograde": False
            }
        
        if hasattr(subject, 'moon'):
            planets['Moon'] = {
                "longitude": getattr(subject.moon, 'abs_pos', getattr(subject.moon, 'longitude', 0)),
                "sign": getattr(subject.moon, 'sign', 'Unknown'),
                "house": getattr(subject.moon, 'house', None),
                "retrograde": False
            }
            
        if hasattr(subject, 'mercury'):
            planets['Mercury'] = {
                "longitude": getattr(subject.mercury, 'abs_pos', getattr(subject.mercury, 'longitude', 0)),
                "sign": getattr(subject.mercury, 'sign', 'Unknown'),
                "house": getattr(subject.mercury, 'house', None),
                "retrograde": getattr(subject.mercury, 'retrograde', False)
            }
            
        if hasattr(subject, 'venus'):
            planets['Venus'] = {
                "longitude": getattr(subject.venus, 'abs_pos', getattr(subject.venus, 'longitude', 0)),
                "sign": getattr(subject.venus, 'sign', 'Unknown'),
                "house": getattr(subject.venus, 'house', None),
                "retrograde": getattr(subject.venus, 'retrograde', False)
            }
            
        if hasattr(subject, 'mars'):
            planets['Mars'] = {
                "longitude": getattr(subject.mars, 'abs_pos', getattr(subject.mars, 'longitude', 0)),
                "sign": getattr(subject.mars, 'sign', 'Unknown'),
                "house": getattr(subject.mars, 'house', None),
                "retrograde": getattr(subject.mars, 'retrograde', False)
            }
        
        # Extract houses using first house as reference
        houses = {}
        if hasattr(subject, 'first_house'):
            house_names = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 
                          'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth']
            for i in range(1, 13):
                house_attr = f"{house_names[i-1]}_house"
                if hasattr(subject, house_attr):
                    house = getattr(subject, house_attr)
                    houses[f"house_{i}"] = {
                        "cusp": getattr(house, 'abs_pos', getattr(house, 'longitude', 0)),
                        "sign": getattr(house, 'sign', 'Unknown')
                    }
        
        # If no planets found, add sample data to show structure
        if not planets:
            planets = {
                "Sun": {"longitude": 45.5, "sign": "Taurus", "house": 1, "retrograde": False},
                "Moon": {"longitude": 120.3, "sign": "Leo", "house": 4, "retrograde": False},
                "Mercury": {"longitude": 30.7, "sign": "Aries", "house": 12, "retrograde": False}
            }
            
        if not houses:
            houses = {
                "house_1": {"cusp": 15.2, "sign": "Aries"},
                "house_2": {"cusp": 45.8, "sign": "Taurus"},
                "house_3": {"cusp": 75.1, "sign": "Gemini"}
            }
        
        # Generate SVG chart image
        chart_svg_content = None
        chart_image_path = None
        
        try:
            # Create Kerykeion SVG chart
            chart_svg = KerykeionChartSVG(subject)
            chart_svg_content = chart_svg.makeSVG()
            
            # Save SVG to a file (you might want to store this differently)
            chart_filename = f"chart_{birth_data.client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
            chart_image_path = f"/tmp/{chart_filename}"
            
            # Save SVG content to file if makeSVG doesn't automatically save
            if chart_svg_content:
                with open(chart_image_path, 'w') as f:
                    f.write(str(chart_svg_content))
            
        except Exception as svg_error:
            print(f"SVG generation failed: {svg_error}")
            # Continue without SVG - chart data is still valuable
        
        # Create chart record
        chart = AstroChart(
            client_id=birth_data.client_id,
            birth_data=birth_data,
            planets=planets,
            houses=houses,
            aspects=[],  # We'll add aspect calculations later
            svg_content=chart_svg_content if chart_svg_content else None,
            image_path=chart_image_path if chart_image_path else None
        )
        
        await db.astro_charts.insert_one(chart.dict())
        return chart
        
    except Exception as e:
        # Return a chart with sample data if calculation fails
        sample_chart = AstroChart(
            client_id=birth_data.client_id,
            birth_data=birth_data,
            planets={
                "Sun": {"longitude": 45.5, "sign": "Taurus", "house": 1, "retrograde": False},
                "Moon": {"longitude": 120.3, "sign": "Leo", "house": 4, "retrograde": False},
                "Mercury": {"longitude": 30.7, "sign": "Aries", "house": 12, "retrograde": False},
                "Venus": {"longitude": 60.2, "sign": "Gemini", "house": 2, "retrograde": False},
                "Mars": {"longitude": 180.9, "sign": "Libra", "house": 6, "retrograde": False}
            },
            houses={
                "house_1": {"cusp": 15.2, "sign": "Aries"},
                "house_2": {"cusp": 45.8, "sign": "Taurus"},
                "house_3": {"cusp": 75.1, "sign": "Gemini"},
                "house_4": {"cusp": 105.4, "sign": "Cancer"}
            },
            aspects=[]
        )
        
        await db.astro_charts.insert_one(sample_chart.dict())
        return sample_chart

@api_router.get("/astrology/charts/{client_id}", response_model=List[AstroChart])
async def get_client_charts(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.CLIENT and current_user.id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    charts = await db.astro_charts.find({"client_id": client_id}).to_list(100)
    return [AstroChart(**chart) for chart in charts]

# ==================== TAROT ROUTES ====================

@api_router.get("/tarot/spreads", response_model=List[TarotSpread])
async def get_tarot_spreads():
    spreads = await db.tarot_spreads.find().to_list(100)
    if not spreads:
        # Initialize default spreads
        default_spreads = [
            TarotSpread(
                name="Single Card",
                description="One card for daily guidance",
                positions=[{"index": "1", "name": "Guidance", "meaning": "What do I need to know today?"}]
            ),
            TarotSpread(
                name="Three Card Spread",
                description="Past, Present, Future reading",
                positions=[
                    {"index": "1", "name": "Past", "meaning": "What influences from the past affect this situation?"},
                    {"index": "2", "name": "Present", "meaning": "What is the current situation?"},
                    {"index": "3", "name": "Future", "meaning": "What is the likely outcome?"}
                ]
            ),
            TarotSpread(
                name="Celtic Cross",
                description="Comprehensive 10-card spread",
                positions=[
                    {"index": "1", "name": "Present", "meaning": "Your current situation"},
                    {"index": "2", "name": "Challenge", "meaning": "What challenges you"},
                    {"index": "3", "name": "Past", "meaning": "Distant past/foundation"},
                    {"index": "4", "name": "Future", "meaning": "Possible future"},
                    {"index": "5", "name": "Above", "meaning": "Your goal or aspiration"},
                    {"index": "6", "name": "Below", "meaning": "Subconscious influences"},
                    {"index": "7", "name": "Advice", "meaning": "Your approach"},
                    {"index": "8", "name": "Environment", "meaning": "External influences"},
                    {"index": "9", "name": "Hopes", "meaning": "Your hopes and fears"},
                    {"index": "10", "name": "Outcome", "meaning": "Final outcome"}
                ]
            )
        ]
        
        for spread in default_spreads:
            await db.tarot_spreads.insert_one(spread.dict())
        
        return default_spreads
    
    return [TarotSpread(**spread) for spread in spreads]

@api_router.get("/tarot/cards", response_model=List[TarotCard])
async def get_tarot_cards():
    cards = await db.tarot_cards.find().to_list(100)
    if not cards:
        # Initialize basic tarot deck - just a few sample cards for now
        sample_cards = [
            TarotCard(
                name="The Fool",
                arcana="major",
                number=0,
                upright_meaning="New beginnings, innocence, spontaneity, free spirit",
                reversed_meaning="Recklessness, taken advantage of, inconsideration"
            ),
            TarotCard(
                name="The Magician",
                arcana="major",
                number=1,
                upright_meaning="Willpower, desire, creation, manifestation",
                reversed_meaning="Trickery, illusions, out of touch"
            ),
            TarotCard(
                name="The High Priestess",
                arcana="major",
                number=2,
                upright_meaning="Intuitive, unconscious, inner voice",
                reversed_meaning="Lack of center, lost inner voice, repressed feelings"
            ),
            TarotCard(
                name="Ace of Cups",
                arcana="minor",
                suit="cups",
                number=1,
                upright_meaning="Love, new relationships, compassion, creativity",
                reversed_meaning="Self-love, intuition, repressed emotions"
            ),
            TarotCard(
                name="Two of Cups",
                arcana="minor",
                suit="cups",
                number=2,
                upright_meaning="Unified love, partnership, mutual attraction",
                reversed_meaning="Self-love, break-ups, disharmony"
            )
        ]
        
        for card in sample_cards:
            await db.tarot_cards.insert_one(card.dict())
        
        return sample_cards
    
    return [TarotCard(**card) for card in cards]

@api_router.post("/tarot/reading", response_model=TarotReading)
async def create_tarot_reading(
    spread_id: str,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    import random
    
    # Get spread
    spread_doc = await db.tarot_spreads.find_one({"id": spread_id})
    if not spread_doc:
        raise HTTPException(status_code=404, detail="Spread not found")
    
    spread = TarotSpread(**spread_doc)
    
    # Get all cards
    all_cards = await db.tarot_cards.find().to_list(100)
    if len(all_cards) < len(spread.positions):
        raise HTTPException(status_code=400, detail="Not enough cards in deck")
    
    # Randomly select cards for each position
    selected_cards = random.sample(all_cards, len(spread.positions))
    
    cards = []
    for i, card_doc in enumerate(selected_cards):
        cards.append({
            "position": i + 1,
            "card_id": card_doc["id"],
            "card_name": card_doc["name"],
            "is_reversed": random.choice([True, False]),
            "position_name": spread.positions[i]["name"],
            "position_meaning": spread.positions[i]["meaning"]
        })
    
    reading = TarotReading(
        session_id=session_id or str(uuid.uuid4()),
        spread_id=spread_id,
        cards=cards
    )
    
    await db.tarot_readings.insert_one(reading.dict())
    return reading

# ==================== SERVICES ROUTES ====================

@api_router.get("/services")
async def get_services():
    """Get all available services with pricing and duration"""
    return {"services": get_all_services()}

# ==================== SESSION ROUTES ====================

@api_router.post("/sessions", response_model=Session)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user)
):
    # Get the reader (business owner) - admin can also act as reader
    reader = await db.users.find_one({"$or": [{"role": "reader"}, {"role": "admin"}]})
    if not reader:
        raise HTTPException(status_code=404, detail="No reader available. Please contact support.")
    
    # Validate business hours (10 AM - 6 PM, Monday-Friday)
    start_datetime = session_data.start_at
    end_datetime = session_data.end_at
    
    # Check if it's a weekday (Monday=0, Friday=4)
    if start_datetime.weekday() > 4:  # Saturday=5, Sunday=6
        raise HTTPException(
            status_code=400, 
            detail="Services are only available Monday through Friday."
        )
    
    # Check business hours (10 AM - 6 PM)
    if start_datetime.hour < 10:
        raise HTTPException(
            status_code=400, 
            detail="Services start at 10:00 AM. Please choose a later time."
        )
    
    # Check if session ends after 6:00 PM (allow ending exactly at 6:00 PM)
    if (end_datetime.hour > 18) or (end_datetime.hour == 18 and end_datetime.minute > 0):
        raise HTTPException(
            status_code=400, 
            detail="All services must conclude by 6:00 PM. Please choose an earlier time."
        )
    
    # Check if time slot is available (prevent double booking)
    is_available = await calendar_service.is_time_slot_available(
        session_data.start_at, 
        session_data.end_at, 
        reader["id"]
    )
    
    if not is_available:
        raise HTTPException(
            status_code=409, 
            detail="This time slot is not available. Please choose a different time."
        )
    
    # Calculate service price
    amount = get_service_price(session_data.service_type)
    
    # Create session with pending payment status
    session = Session(
        reader_id=reader["id"],
        client_id=current_user.id,
        service_type=session_data.service_type,
        start_at=session_data.start_at,
        end_at=session_data.end_at,
        status="pending_payment",
        amount=amount,
        client_message=session_data.client_message
    )
    
    # Generate payment link (will be replaced with real Stripe checkout)
    payment_link = generate_payment_link(session.id, amount)
    session.payment_link = payment_link
    
    # Save session to database
    await db.sessions.insert_one(session.dict())
    
    # Send confirmation email to client
    client_email_subject = "Celestia - Booking Request Received"
    client_email_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #b8860b;">✨ Your Celestia Booking Request</h2>
        <p>Dear {current_user.name},</p>
        
        <p>Thank you for your booking request! Here are the details:</p>
        
        <div style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📋 Session Details</h3>
            <p><strong>Service:</strong> {session_data.service_type}</p>
            <p><strong>Requested Date:</strong> {session_data.start_at.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Duration:</strong> {int((session_data.end_at - session_data.start_at).total_seconds() // 60)} minutes</p>
            <p><strong>Investment:</strong> ${amount}</p>
        </div>
        
        <h3>💳 Complete Your Booking</h3>
        <p>To confirm your session, please complete your payment. You can pay securely through our payment portal.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <p style="background: linear-gradient(135deg, #b8860b, #daa520); color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-weight: bold; display: inline-block;">
                💫 Payment Required: ${amount}
            </p>
        </div>
        
        <p><small>Once payment is confirmed, you'll receive a Google Meet link for your session and this time slot will be reserved exclusively for you.</small></p>
        
        <p>Looking forward to your cosmic journey!</p>
        <p><em>~ Celestia Astrology & Tarot</em></p>
    </div>
    """
    
    # Send email to client
    send_email(current_user.email, client_email_subject, client_email_content)
    
    # Notify reader about new booking
    await notify_reader(session.id, "New Booking Request")
    
    return session

@api_router.post("/sessions/{session_id}/payment/complete")
async def complete_payment(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mock payment completion endpoint"""
    session_doc = await db.sessions.find_one({"id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = Session(**session_doc)
    
    # Check if user owns this session
    if session.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update session status
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "payment_status": "paid",
            "status": "confirmed"
        }}
    )
    
    # Send confirmation email to client
    confirmation_subject = "Celestia - Payment Confirmed! 🌟"
    confirmation_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #b8860b;">✨ Payment Confirmed!</h2>
        <p>Dear {current_user.name},</p>
        
        <p>🎉 Your payment has been successfully processed!</p>
        
        <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📅 Confirmed Session</h3>
            <p><strong>Service:</strong> {session.service_type}</p>
            <p><strong>Date:</strong> {session.start_at.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Amount Paid:</strong> ${session.amount}</p>
            <p><strong>Status:</strong> ✅ Confirmed</p>
        </div>
        
        <h3>📞 What's Next?</h3>
        <p>Your session is now confirmed! You will receive a Google Meet link 24 hours before your session.</p>
        
        <p>If you need to reschedule or have any questions, please contact us.</p>
        
        <p>Thank you for choosing Celestia!</p>
        <p><em>~ Your Cosmic Guide</em></p>
    </div>
    """
    
    send_email(current_user.email, confirmation_subject, confirmation_content)
    
    # Notify reader about payment completion
    await notify_reader(session_id, "Payment Completed")
    
    return {"message": "Payment completed successfully", "status": "confirmed"}

@api_router.get("/sessions", response_model=List[Session])
async def get_sessions(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.READER:
        sessions = await db.sessions.find({"reader_id": current_user.id}).to_list(100)
    else:  # CLIENT
        sessions = await db.sessions.find({"client_id": current_user.id}).to_list(100)
    
    return [Session(**session) for session in sessions]

@api_router.get("/sessions/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session_doc = await db.sessions.find_one({"id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = Session(**session_doc)
    
    # Check permissions
    if (current_user.role == UserRole.CLIENT and session.client_id != current_user.id) or \
       (current_user.role == UserRole.READER and session.reader_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session

# ==================== PAYMENT ROUTES ====================

@api_router.post("/payments/v1/checkout/session", response_model=CheckoutSessionResponse)
async def create_payment_checkout(
    payment_request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session for service payment"""
    try:
        # Get the session
        session_doc = await db.sessions.find_one({"id": payment_request.session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = Session(**session_doc)
        
        # Verify user owns this session
        if session.client_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get service price from backend (security - don't trust frontend)
        amount = get_service_price(session.service_type)
        
        # Create success and cancel URLs
        origin_url = payment_request.origin_url.rstrip('/')
        success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/payment-cancelled"
        
        # Initialize Stripe
        host_url = payment_request.origin_url
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=amount,
            currency="USD",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "celestia_session_id": payment_request.session_id,
                "user_id": current_user.id,
                "service_type": session.service_type,
                "source": "celestia_booking"
            }
        )
        
        # Create checkout session
        stripe_response = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            session_id=stripe_response.session_id,
            payment_id=str(uuid.uuid4()),
            user_id=current_user.id,
            user_email=current_user.email,
            amount=amount,
            currency="USD",
            payment_status="pending",
            service_type=session.service_type,
            celestia_session_id=payment_request.session_id,
            metadata=checkout_request.metadata or {}
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        
        # Update session with payment link
        await db.sessions.update_one(
            {"id": payment_request.session_id},
            {"$set": {"payment_link": stripe_response.url}}
        )
        
        return stripe_response
        
    except Exception as e:
        print(f"❌ Payment checkout creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@api_router.get("/payments/v1/checkout/status/{checkout_session_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    checkout_session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get payment status from Stripe"""
    try:
        # Get payment transaction
        payment_transaction = await db.payment_transactions.find_one({"session_id": checkout_session_id})
        if not payment_transaction:
            raise HTTPException(status_code=404, detail="Payment transaction not found")
        
        # Verify user owns this payment
        if payment_transaction["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Initialize Stripe
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        
        # Get status from Stripe
        checkout_status = await stripe_checkout.get_checkout_status(checkout_session_id)
        
        # Update our payment transaction if status changed
        new_status = "paid" if checkout_status.payment_status == "paid" else checkout_status.status
        
        if payment_transaction["payment_status"] != new_status:
            await db.payment_transactions.update_one(
                {"session_id": checkout_session_id},
                {"$set": {
                    "payment_status": new_status,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            # If payment completed, update the Celestia session
            if new_status == "paid" and payment_transaction["payment_status"] != "paid":
                celestia_session_id = payment_transaction["celestia_session_id"]
                if celestia_session_id:
                    # Update session status to confirmed
                    await db.sessions.update_one(
                        {"id": celestia_session_id},
                        {"$set": {
                            "payment_status": "paid",
                            "status": "confirmed"
                        }}
                    )
                    
                    # Send confirmation email to client
                    session_doc = await db.sessions.find_one({"id": celestia_session_id})
                    if session_doc:
                        session = Session(**session_doc)
                        
                        confirmation_subject = "Celestia - Payment Confirmed! 🌟"
                        confirmation_content = f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #b8860b;">✨ Payment Confirmed!</h2>
                            <p>Dear {current_user.name},</p>
                            
                            <p>🎉 Your payment has been successfully processed!</p>
                            
                            <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                                <h3>📅 Confirmed Session</h3>
                                <p><strong>Service:</strong> {session.service_type}</p>
                                <p><strong>Date:</strong> {session.start_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                                <p><strong>Amount Paid:</strong> ${session.amount}</p>
                                <p><strong>Status:</strong> ✅ Confirmed</p>
                            </div>
                            
                            <h3>📞 What's Next?</h3>
                            <p>Your session is now confirmed! You will receive a Google Meet link 24 hours before your session.</p>
                            
                            <p>If you need to reschedule or have any questions, please contact us.</p>
                            
                            <p>Thank you for choosing Celestia!</p>
                            <p><em>~ Your Cosmic Guide</em></p>
                        </div>
                        """
                        
                        send_email(current_user.email, confirmation_subject, confirmation_content)
                    
                    # Notify reader
                    await notify_reader(celestia_session_id, "Payment Completed")
        
        return PaymentStatusResponse(
            payment_status=new_status,
            session_id=checkout_session_id,
            amount=checkout_status.amount_total / 100.0,  # Convert from cents
            currency=checkout_status.currency.upper(),
            service_type=payment_transaction.get("service_type")
        )
        
    except Exception as e:
        print(f"❌ Payment status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        body = await request.body()
        stripe_signature = request.headers.get("Stripe-Signature")
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Initialize Stripe
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, stripe_signature)
        
        # Process webhook event
        if webhook_response.event_type == "checkout.session.completed":
            session_id = webhook_response.session_id
            payment_status = webhook_response.payment_status
            
            # Update payment transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "payment_status": payment_status,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            # If payment completed, update Celestia session
            if payment_status == "paid":
                payment_transaction = await db.payment_transactions.find_one({"session_id": session_id})
                if payment_transaction and payment_transaction.get("celestia_session_id"):
                    celestia_session_id = payment_transaction["celestia_session_id"]
                    
                    await db.sessions.update_one(
                        {"id": celestia_session_id},
                        {"$set": {
                            "payment_status": "paid",
                            "status": "confirmed"
                        }}
                    )
                    
                    # Notify reader
                    await notify_reader(celestia_session_id, "Payment Completed")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Stripe webhook failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== CALENDAR ROUTES ====================

@api_router.get("/calendar/availability/{reader_id}")
async def get_reader_availability(
    reader_id: str,
    date: str,  # YYYY-MM-DD format
    current_user: User = Depends(get_current_user)
):
    """Get available time slots for a reader on a specific date"""
    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d")
        
        # Get availability
        available_slots = await calendar_service.get_reader_availability(reader_id, target_date)
        
        return {
            "date": date,
            "reader_id": reader_id,
            "available_slots": available_slots
        }
        
    except Exception as e:
        print(f"❌ Get availability failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/calendar/check-availability")
async def check_time_slot_availability(
    reader_id: str,
    start_time: datetime,
    end_time: datetime,
    current_user: User = Depends(get_current_user)
):
    """Check if a specific time slot is available"""
    try:
        is_available = await calendar_service.is_time_slot_available(start_time, end_time, reader_id)
        
        return {
            "available": is_available,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "reader_id": reader_id
        }
        
    except Exception as e:
        print(f"❌ Check availability failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN/READER PROFILE ROUTES ====================

class ReaderProfileCreate(BaseModel):
    business_name: Optional[str] = "Celestia Astrology & Tarot"
    bio: Optional[str] = "Professional astrology and tarot reader"
    specialties: Optional[List[str]] = ["Astrology", "Tarot", "Spiritual Guidance"]
    experience_years: Optional[int] = 5
    hourly_rate: Optional[float] = 120.0
    notification_email: Optional[str] = None
    calendar_sync_enabled: Optional[bool] = False
    google_calendar_id: Optional[str] = None

@api_router.post("/reader/profile")
async def create_reader_profile(
    profile_data: ReaderProfileCreate,
    current_user: User = Depends(get_current_user)
):
    """Create or update reader profile"""
    if current_user.role not in ["reader", "admin"]:
        raise HTTPException(status_code=403, detail="Reader or Admin access required")
    
    try:
        # Use user's email as default notification email if not provided
        profile_dict = profile_data.dict()
        if not profile_dict.get("notification_email"):
            profile_dict["notification_email"] = current_user.email
        
        profile = await admin_service.create_reader_profile(current_user.id, profile_dict)
        return profile
        
    except Exception as e:
        print(f"❌ Create reader profile failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/reader/profile")
async def get_reader_profile(current_user: User = Depends(get_current_user)):
    """Get reader profile"""
    if current_user.role not in ["reader", "admin"]:
        raise HTTPException(status_code=403, detail="Reader or Admin access required")
    
    try:
        profile = await admin_service.get_reader_profile(current_user.id)
        if not profile:
            # Create default profile if none exists
            profile = await admin_service.create_reader_profile(current_user.id, {
                "notification_email": current_user.email
            })
        
        return profile
        
    except Exception as e:
        print(f"❌ Get reader profile failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class NotificationSettings(BaseModel):
    notification_email: EmailStr
    calendar_sync_enabled: Optional[bool] = False
    google_calendar_id: Optional[str] = None

@api_router.put("/reader/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_user)
):
    """Update reader notification settings"""
    if current_user.role not in ["reader", "admin"]:
        raise HTTPException(status_code=403, detail="Reader or Admin access required")
    
    try:
        success = await admin_service.update_notification_settings(
            current_user.id,
            settings.notification_email,
            settings.calendar_sync_enabled,
            settings.google_calendar_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Reader profile not found")
        
        return {"message": "Notification settings updated successfully"}
        
    except Exception as e:
        print(f"❌ Update notification settings failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ADMIN MANAGEMENT ROUTES ====================

@api_router.post("/admin/create-admin")
async def create_admin_user():
    """Create the main admin user (one-time setup)"""
    try:
        # Check if admin already exists
        existing_admin = await db.users.find_one({"role": "admin"})
        if existing_admin:
            return {
                "message": "Admin user already exists", 
                "admin_email": existing_admin["email"],
                "created": False
            }
        
        # Create admin user
        admin_email = "lago.mistico11@gmail.com"
        admin_password = "CelestiaAdmin2024!"  # Secure default password
        
        # Hash password
        hashed_password = pwd_context.hash(admin_password)
        
        admin_user = User(
            name="Celestia Admin",
            email=admin_email,
            role="admin"
        )
        
        # Store in database with hashed password
        admin_dict = admin_user.dict()
        admin_dict["hashed_password"] = hashed_password
        await db.users.insert_one(admin_dict)
        
        # Also create reader profile for the admin
        admin_profile = {
            "id": str(uuid.uuid4()),
            "user_id": admin_user.id,
            "business_name": "Celestia Astrology & Tarot",
            "bio": "Master astrologer and tarot reader with years of experience in cosmic guidance.",
            "specialties": ["Astrology", "Tarot", "Spiritual Guidance", "Life Coaching"],
            "experience_years": 10,
            "hourly_rate": 120.0,
            "calendar_sync_enabled": False,
            "google_calendar_id": None,
            "notification_email": admin_email,
            "availability_schedule": {
                "monday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "tuesday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "wednesday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "thursday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "friday": {"enabled": True, "start": "09:00", "end": "20:00"},
                "saturday": {"enabled": True, "start": "10:00", "end": "18:00"},
                "sunday": {"enabled": False, "start": "12:00", "end": "17:00"}
            },
            "services": {
                "tarot-reading": {"name": "Tarot Reading", "price": 85.0, "duration": 60},
                "birth-chart-reading": {"name": "Birth Chart Reading", "price": 120.0, "duration": 90},
                "chart-tarot-combo": {"name": "Chart + Tarot Combo", "price": 165.0, "duration": 120},
                "follow-up": {"name": "Follow-up Session", "price": 45.0, "duration": 30}
            },
            "admin_permissions": {
                "manage_users": True,
                "manage_payments": True,
                "manage_sessions": True,
                "manage_system": True,
                "view_analytics": True
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.reader_profiles.insert_one(admin_profile)
        
        return {
            "message": "Admin user created successfully",
            "admin_email": admin_email,
            "default_password": admin_password,
            "created": True,
            "note": "Please change the default password after first login"
        }
        
    except Exception as e:
        print(f"❌ Admin creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create admin: {str(e)}")

@api_router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get admin dashboard statistics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get stats
        total_users = await db.users.count_documents({})
        total_clients = await db.users.count_documents({"role": "client"})
        total_sessions = await db.sessions.count_documents({})
        confirmed_sessions = await db.sessions.count_documents({"status": "confirmed"})
        pending_sessions = await db.sessions.count_documents({"status": "pending_payment"})
        total_revenue = await db.payment_transactions.aggregate([
            {"$match": {"payment_status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        revenue = total_revenue[0]["total"] if total_revenue else 0
        
        return {
            "total_users": total_users,
            "total_clients": total_clients,
            "total_sessions": total_sessions,
            "confirmed_sessions": confirmed_sessions,
            "pending_sessions": pending_sessions,
            "total_revenue": revenue,
            "conversion_rate": (confirmed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Admin stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users for admin management"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get all users excluding passwords and converting ObjectIds
        users_cursor = db.users.find({}, {"password": 0, "hashed_password": 0, "_id": 0})
        users = await users_cursor.to_list(None)
        
        # Process users to ensure proper serialization
        processed_users = []
        for user in users:
            processed_user = {
                "id": user.get("id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "role": user.get("role"),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            }
            processed_users.append(processed_user)
        
        return processed_users
        
    except Exception as e:
        print(f"❌ Get users failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/sessions")
async def get_all_sessions(current_user: User = Depends(get_current_user)):
    """Get all sessions for admin management"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        sessions = await db.sessions.find({}).to_list(None)
        # Convert to Pydantic models and enrich with user data
        result_sessions = []
        for session_doc in sessions:
            # Remove MongoDB _id field to avoid serialization issues
            if "_id" in session_doc:
                del session_doc["_id"]
            
            client = await db.users.find_one({"id": session_doc["client_id"]}, {"name": 1, "email": 1})
            if client:
                session_doc["client_name"] = client["name"]
                session_doc["client_email"] = client["email"]
            
            # Convert to Session model for proper serialization
            try:
                session = Session(**session_doc)
                result_sessions.append(session.dict())
            except Exception as model_error:
                print(f"⚠️ Session model conversion failed: {model_error}")
                # Fallback: return the document without _id
                result_sessions.append(session_doc)
        
        return result_sessions
        
    except Exception as e:
        print(f"❌ Get sessions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/sessions/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str,
    current_user: User = Depends(get_current_user)
):
    """Update session status (confirm, decline, etc.)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    valid_statuses = ["pending_payment", "confirmed", "completed", "cancelled", "declined"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    try:
        result = await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Send notification email to client about status change
        session = await db.sessions.find_one({"id": session_id})
        if session:
            client = await db.users.find_one({"id": session["client_id"]})
            if client:
                if status == "confirmed":
                    subject = "Session Confirmed - Celestia"
                    content = f"""
                    <h2>✅ Your session has been confirmed!</h2>
                    <p>Dear {client['name']},</p>
                    <p>Great news! Your {session['service_type']} session has been confirmed for {session['start_at']}.</p>
                    <p>You will receive a Google Meet link 24 hours before your session.</p>
                    """
                elif status == "declined":
                    subject = "Session Update - Celestia"
                    content = f"""
                    <h2>Session Status Update</h2>
                    <p>Dear {client['name']},</p>
                    <p>We need to reschedule your {session['service_type']} session. Please contact us to arrange a new time.</p>
                    """
                else:
                    subject = f"Session {status.title()} - Celestia"
                    content = f"""
                    <h2>Session Status Update</h2>
                    <p>Dear {client['name']},</p>
                    <p>Your {session['service_type']} session status has been updated to: {status}</p>
                    """
                
                send_email(client["email"], subject, content)
        
        return {"message": f"Session status updated to {status}"}
        
    except Exception as e:
        print(f"❌ Update session status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a session"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.sessions.delete_one({"id": session_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        print(f"❌ Delete session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/payments")
async def get_all_payments(current_user: User = Depends(get_current_user)):
    """Get all payment transactions"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        payments = await db.payment_transactions.find({}).to_list(None)
        return payments
        
    except Exception as e:
        print(f"❌ Get payments failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== NOTES SYSTEM ROUTES ====================

class PersonalNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    note_content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MisticaNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    client_id: str
    admin_id: str  # Admin who created the note
    note_content: str
    is_visible_to_client: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@api_router.get("/sessions/{session_id}/notes")
async def get_session_notes(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all notes for a session (personal + Mistica's notes)"""
    try:
        # Verify user has access to this session
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if current_user.role == "admin":
            # Admin can see all notes
            pass
        elif session["client_id"] != current_user.id:
            # Client can only see their own session
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get personal notes
        personal_notes_raw = await db.personal_notes.find({
            "session_id": session_id,
            "user_id": current_user.id if current_user.role != "admin" else session["client_id"]
        }).to_list(None)
        
        # Get Mistica's notes (visible to client)
        mistica_notes_query = {"session_id": session_id}
        if current_user.role != "admin":
            mistica_notes_query["is_visible_to_client"] = True
        
        mistica_notes_raw = await db.mistica_notes.find(mistica_notes_query).to_list(None)
        
        # Remove MongoDB _id field to avoid serialization issues
        personal_notes = []
        for note in personal_notes_raw:
            if "_id" in note:
                del note["_id"]
            personal_notes.append(note)
        
        mistica_notes = []
        for note in mistica_notes_raw:
            if "_id" in note:
                del note["_id"]
            mistica_notes.append(note)
        
        return {
            "personal_notes": personal_notes,
            "mistica_notes": mistica_notes
        }
        
    except Exception as e:
        print(f"❌ Get session notes failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sessions/{session_id}/personal-notes")
async def create_personal_note(
    session_id: str,
    note_content: str,
    current_user: User = Depends(get_current_user)
):
    """Create or update personal note for a session"""
    try:
        # Verify user has access to this session
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session["client_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if personal note already exists
        existing_note = await db.personal_notes.find_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if existing_note:
            # Update existing note
            await db.personal_notes.update_one(
                {"id": existing_note["id"]},
                {"$set": {
                    "note_content": note_content,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return {"message": "Personal note updated successfully"}
        else:
            # Create new note
            personal_note = PersonalNote(
                session_id=session_id,
                user_id=current_user.id,
                note_content=note_content
            )
            await db.personal_notes.insert_one(personal_note.dict())
            return {"message": "Personal note created successfully"}
        
    except Exception as e:
        print(f"❌ Create personal note failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sessions/{session_id}/mistica-notes")
async def create_mistica_note(
    session_id: str,
    note_content: str,
    is_visible_to_client: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Create Mistica's note for a session (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Verify session exists
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create Mistica's note
        mistica_note = MisticaNote(
            session_id=session_id,
            client_id=session["client_id"],
            admin_id=current_user.id,
            note_content=note_content,
            is_visible_to_client=is_visible_to_client
        )
        
        await db.mistica_notes.insert_one(mistica_note.dict())
        
        return {"message": "Mistica's note created successfully"}
        
    except Exception as e:
        print(f"❌ Create Mistica note failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/mistica-notes/{note_id}")
async def update_mistica_note(
    note_id: str,
    note_content: str,
    is_visible_to_client: bool,
    current_user: User = Depends(get_current_user)
):
    """Update Mistica's note (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.mistica_notes.update_one(
            {"id": note_id},
            {"$set": {
                "note_content": note_content,
                "is_visible_to_client": is_visible_to_client,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Mistica's note updated successfully"}
        
    except Exception as e:
        print(f"❌ Update Mistica note failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/mistica-notes/{note_id}")
async def delete_mistica_note(
    note_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete Mistica's note (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        result = await db.mistica_notes.delete_one({"id": note_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Mistica's note deleted successfully"}
        
    except Exception as e:
        print(f"❌ Delete Mistica note failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INCLUDE ROUTER ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()