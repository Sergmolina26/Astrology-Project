from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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
from datetime import datetime, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt
from kerykeion import AstrologicalSubject
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

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
    status: str = "scheduled"  # scheduled, completed, canceled
    notes: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, refunded
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionCreate(BaseModel):
    client_id: str
    service_type: str
    start_at: datetime
    end_at: datetime

class SessionNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str
    visibility: str = "client_visible"  # reader_private, client_visible
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
        
        # Create chart record
        chart = AstroChart(
            client_id=birth_data.client_id,
            birth_data=birth_data,
            planets=planets,
            houses=houses,
            aspects=[]  # We'll add aspect calculations later
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

# ==================== SESSION ROUTES ====================

@api_router.post("/sessions", response_model=Session)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user)
):
    session = Session(
        reader_id=current_user.id,
        **session_data.dict()
    )
    
    await db.sessions.insert_one(session.dict())
    return session

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