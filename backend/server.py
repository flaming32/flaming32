from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
import secrets
import string
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
import re
import json
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI setup via Emergent
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Olaoluwa32$"

# Payment details
PAYMENT_INFO = {
    "account_number": "3002978669",
    "bank_name": "KUDA MFB",
    "account_name": "STASHORRA STORE",
    "amount": 400,
    "uses_per_payment": 2,
    "email": "support@stashorra.store"
}

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBasic()

# All brands alphabetically sorted
ALL_BRANDS = [
    "AGM", "Alcatel", "Allview", "Apple", "Archos", "Asus", "Asus ROG",
    "BQ", "Benco", "Black Shark", "Blackview", "Blu",
    "Cat", "Cherry Mobile", "Condor", "Coolpad",
    "Doogee", "Doro",
    "Energizer", "Essential",
    "Fairphone", "Fujitsu",
    "General Mobile", "Gionee", "Google", "Google Pixel",
    "HMD", "HMD Global", "HTC", "Hisense", "Honor", "Huawei",
    "Infinix", "Inoi", "Intex", "Itel", "iQOO",
    "Kyocera",
    "LG", "Lava", "LeEco", "Lenovo",
    "Maxwest", "Meizu", "Micromax", "Motorola", "myPhone",
    "NEC", "Nokia", "Nubia",
    "OnePlus", "Oppo",
    "Palm", "Panasonic", "Philips", "Poco", "Prestigio",
    "QMobile",
    "Razer", "Realme", "Redmi",
    "Samsung", "Sharp", "Sico", "Sony", "Symphony",
    "TCL", "Tecno", "Transsion",
    "Ulefone", "Umidigi",
    "Vertu", "Vivo", "Vsmart",
    "Wiko",
    "Xiaomi",
    "ZTE", "ZUK"
]

# Models
class PhoneSearchRequest(BaseModel):
    brand: str
    model: str

class PhoneConditionExtended(BaseModel):
    screen_condition: str
    body_condition: str
    battery_health: str
    face_id_working: Optional[str] = None
    touch_id_working: Optional[str] = None
    icloud_status: Optional[str] = None
    back_glass_condition: Optional[str] = None
    true_tone_working: Optional[str] = None
    fingerprint_working: Optional[str] = None
    face_unlock_working: Optional[str] = None
    frp_status: Optional[str] = None
    charging_port: Optional[str] = None
    speakers_working: str = "yes"
    cameras_working: str = "yes"
    buttons_working: str = "yes"
    network_status: str = "unlocked"
    original_parts: str = "yes"

class PriceEstimateRequest(BaseModel):
    brand: str
    model: str
    condition: PhoneConditionExtended
    new_price: Optional[float] = None
    used_price: Optional[float] = None
    access_code: str

class PriceData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str
    price: Optional[float] = None
    currency: str = "NGN"
    url: Optional[str] = None
    title: Optional[str] = None

class ScrapedPrices(BaseModel):
    model_config = ConfigDict(extra="ignore")
    new_prices: List[PriceData]
    used_prices: List[PriceData]

class PriceEstimate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: str
    model: str
    condition: Dict[str, Any]
    new_price_avg: Optional[float] = None
    used_price_avg: Optional[float] = None
    estimated_price: float
    confidence: str
    reasoning: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccessCodeCreate(BaseModel):
    note: Optional[str] = None

class AccessCodeVerify(BaseModel):
    code: str

class AdminLogin(BaseModel):
    username: str
    password: str

# iPhone biometric info
IPHONE_FACE_ID_MODELS = [
    "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
    "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
    "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13", "iPhone 13 Mini",
    "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12", "iPhone 12 Mini",
    "iPhone 11 Pro Max", "iPhone 11 Pro", "iPhone 11",
    "iPhone XS Max", "iPhone XS", "iPhone XR", "iPhone X"
]

IPHONE_TOUCH_ID_MODELS = [
    "iPhone SE (2022)", "iPhone SE (2020)", "iPhone SE",
    "iPhone 8 Plus", "iPhone 8",
    "iPhone 7 Plus", "iPhone 7",
    "iPhone 6s Plus", "iPhone 6s",
    "iPhone 6 Plus", "iPhone 6"
]

# Reference prices
REFERENCE_PRICES = {
    "Apple": {
        "iPhone 15 Pro Max": {"new": 2200000, "used": 1100000},
        "iPhone 15 Pro": {"new": 1900000, "used": 950000},
        "iPhone 15 Plus": {"new": 1500000, "used": 750000},
        "iPhone 15": {"new": 1400000, "used": 680000},
        "iPhone 14 Pro Max": {"new": 1600000, "used": 700000},
        "iPhone 14 Pro": {"new": 1400000, "used": 600000},
        "iPhone 14 Plus": {"new": 1100000, "used": 500000},
        "iPhone 14": {"new": 1000000, "used": 450000},
        "iPhone 13 Pro Max": {"new": 1200000, "used": 480000},
        "iPhone 13 Pro": {"new": 1000000, "used": 400000},
        "iPhone 13": {"new": 750000, "used": 300000},
        "iPhone 13 Mini": {"new": 650000, "used": 250000},
        "iPhone 12 Pro Max": {"new": 850000, "used": 320000},
        "iPhone 12 Pro": {"new": 700000, "used": 270000},
        "iPhone 12": {"new": 550000, "used": 200000},
        "iPhone 12 Mini": {"new": 450000, "used": 160000},
        "iPhone 11 Pro Max": {"new": 650000, "used": 230000},
        "iPhone 11 Pro": {"new": 550000, "used": 190000},
        "iPhone 11": {"new": 420000, "used": 150000},
        "iPhone XS Max": {"new": 450000, "used": 140000},
        "iPhone XS": {"new": 380000, "used": 110000},
        "iPhone XR": {"new": 320000, "used": 100000},
        "iPhone X": {"new": 300000, "used": 90000},
        "iPhone SE (2022)": {"new": 450000, "used": 180000},
        "iPhone SE (2020)": {"new": 320000, "used": 110000},
        "iPhone 8 Plus": {"new": 280000, "used": 80000},
        "iPhone 8": {"new": 220000, "used": 65000},
        "iPhone 7 Plus": {"new": 200000, "used": 55000},
        "iPhone 7": {"new": 150000, "used": 40000},
    },
    "Samsung": {
        "Galaxy S24 Ultra": {"new": 2100000, "used": 1050000},
        "Galaxy S24+": {"new": 1500000, "used": 700000},
        "Galaxy S24": {"new": 1200000, "used": 550000},
        "Galaxy S23 Ultra": {"new": 1500000, "used": 600000},
        "Galaxy S23+": {"new": 1100000, "used": 450000},
        "Galaxy S23": {"new": 900000, "used": 350000},
        "Galaxy S22 Ultra": {"new": 1000000, "used": 380000},
        "Galaxy S22+": {"new": 750000, "used": 280000},
        "Galaxy S22": {"new": 600000, "used": 220000},
        "Galaxy S21 Ultra": {"new": 750000, "used": 260000},
        "Galaxy S21+": {"new": 550000, "used": 180000},
        "Galaxy S21": {"new": 450000, "used": 150000},
        "Galaxy Z Fold 5": {"new": 2800000, "used": 1400000},
        "Galaxy Z Fold 4": {"new": 2000000, "used": 850000},
        "Galaxy Z Flip 5": {"new": 1300000, "used": 550000},
        "Galaxy Z Flip 4": {"new": 900000, "used": 350000},
        "Galaxy A54": {"new": 380000, "used": 150000},
        "Galaxy A34": {"new": 280000, "used": 110000},
        "Galaxy A24": {"new": 200000, "used": 80000},
        "Galaxy A14": {"new": 150000, "used": 55000},
        "Galaxy A04": {"new": 100000, "used": 35000},
    },
    "Tecno": {
        "Phantom X2 Pro": {"new": 550000, "used": 220000},
        "Phantom X2": {"new": 450000, "used": 170000},
        "Phantom V Fold": {"new": 900000, "used": 400000},
        "Phantom V Flip": {"new": 550000, "used": 220000},
        "Camon 30 Pro": {"new": 350000, "used": 140000},
        "Camon 30": {"new": 280000, "used": 110000},
        "Camon 20 Pro": {"new": 280000, "used": 100000},
        "Camon 20": {"new": 180000, "used": 65000},
        "Camon 19 Pro": {"new": 200000, "used": 70000},
        "Camon 19": {"new": 150000, "used": 50000},
        "Spark 20 Pro+": {"new": 220000, "used": 85000},
        "Spark 20 Pro": {"new": 180000, "used": 65000},
        "Spark 20": {"new": 130000, "used": 45000},
        "Spark 10 Pro": {"new": 150000, "used": 50000},
        "Spark 10": {"new": 100000, "used": 35000},
        "Pova 6 Pro": {"new": 280000, "used": 110000},
        "Pova 6": {"new": 200000, "used": 75000},
        "Pova 5 Pro": {"new": 200000, "used": 70000},
        "Pova 5": {"new": 160000, "used": 55000},
        "Pop 8": {"new": 80000, "used": 28000},
        "Pop 7": {"new": 65000, "used": 22000},
    },
    "Infinix": {
        "Zero 30": {"new": 350000, "used": 140000},
        "Zero 20": {"new": 280000, "used": 100000},
        "Note 40 Pro": {"new": 320000, "used": 125000},
        "Note 40": {"new": 250000, "used": 95000},
        "Note 30 Pro": {"new": 220000, "used": 80000},
        "Note 30": {"new": 170000, "used": 60000},
        "Hot 40 Pro": {"new": 180000, "used": 65000},
        "Hot 40": {"new": 140000, "used": 50000},
        "Hot 30": {"new": 120000, "used": 42000},
        "Smart 8": {"new": 95000, "used": 32000},
    },
    "Itel": {
        "S24": {"new": 130000, "used": 45000},
        "S23": {"new": 90000, "used": 30000},
        "P55": {"new": 80000, "used": 28000},
        "A70": {"new": 85000, "used": 28000},
        "A60": {"new": 65000, "used": 22000},
    },
    "Xiaomi": {
        "14 Ultra": {"new": 1800000, "used": 800000},
        "14 Pro": {"new": 1200000, "used": 500000},
        "14": {"new": 900000, "used": 380000},
        "13 Ultra": {"new": 1200000, "used": 450000},
        "13 Pro": {"new": 900000, "used": 340000},
        "13": {"new": 650000, "used": 250000},
    },
    "Redmi": {
        "Note 13 Pro+": {"new": 380000, "used": 150000},
        "Note 13 Pro": {"new": 300000, "used": 115000},
        "Note 13": {"new": 220000, "used": 80000},
        "Note 12 Pro": {"new": 260000, "used": 95000},
        "Note 12": {"new": 180000, "used": 65000},
    },
    "Poco": {
        "X6 Pro": {"new": 450000, "used": 180000},
        "X6": {"new": 350000, "used": 140000},
        "X5 Pro": {"new": 320000, "used": 120000},
        "M6 Pro": {"new": 200000, "used": 75000},
    },
    "Google": {
        "Pixel 8 Pro": {"new": 1100000, "used": 480000},
        "Pixel 8": {"new": 800000, "used": 320000},
        "Pixel 7 Pro": {"new": 750000, "used": 280000},
        "Pixel 7": {"new": 550000, "used": 200000},
    },
    "OnePlus": {
        "12": {"new": 1200000, "used": 520000},
        "11": {"new": 900000, "used": 340000},
        "Nord 3": {"new": 450000, "used": 170000},
    },
    "Oppo": {
        "Find X7 Ultra": {"new": 1500000, "used": 650000},
        "Reno 11 Pro": {"new": 650000, "used": 260000},
        "Reno 11": {"new": 480000, "used": 180000},
        "A78": {"new": 250000, "used": 90000},
    },
    "Vivo": {
        "X100 Pro": {"new": 1300000, "used": 550000},
        "V30 Pro": {"new": 650000, "used": 260000},
        "Y100": {"new": 280000, "used": 105000},
    },
    "Realme": {
        "GT 5 Pro": {"new": 800000, "used": 320000},
        "12 Pro+": {"new": 500000, "used": 190000},
        "C67": {"new": 180000, "used": 65000},
    },
    "Huawei": {
        "Mate 60 Pro": {"new": 1500000, "used": 650000},
        "P60 Pro": {"new": 1100000, "used": 450000},
        "Nova 12 Pro": {"new": 550000, "used": 210000},
    },
    "Honor": {
        "Magic 6 Pro": {"new": 1200000, "used": 500000},
        "90 Pro": {"new": 650000, "used": 250000},
    },
    "Nokia": {
        "G42": {"new": 200000, "used": 70000},
        "C32": {"new": 100000, "used": 35000},
    },
    "Motorola": {
        "Edge 40 Pro": {"new": 750000, "used": 300000},
        "G84": {"new": 350000, "used": 130000},
    },
}

def is_iphone(brand: str) -> bool:
    return brand.lower() == "apple"

def get_iphone_biometric_type(model: str) -> str:
    if model in IPHONE_FACE_ID_MODELS:
        return "face_id"
    elif model in IPHONE_TOUCH_ID_MODELS:
        return "touch_id"
    else:
        return "face_id"

def get_reference_prices(brand: str, model: str) -> dict:
    brand_prices = REFERENCE_PRICES.get(brand, {})
    return brand_prices.get(model, {"new": None, "used": None})

def generate_access_code():
    """Generate a unique 8-character access code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))

# Access Code Functions
async def verify_access_code(code: str) -> dict:
    """Verify access code and return usage info"""
    access_code = await db.access_codes.find_one({"code": code.upper()})
    if not access_code:
        return {"valid": False, "message": "Invalid access code"}
    
    if access_code.get("uses_remaining", 0) <= 0:
        return {"valid": False, "message": "Access code has been exhausted. Please purchase a new one."}
    
    return {
        "valid": True,
        "uses_remaining": access_code.get("uses_remaining", 0),
        "message": "Access code valid"
    }

async def use_access_code(code: str) -> bool:
    """Decrement usage count for access code"""
    result = await db.access_codes.update_one(
        {"code": code.upper(), "uses_remaining": {"$gt": 0}},
        {"$inc": {"uses_remaining": -1}, "$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
    )
    return result.modified_count > 0

# Web Scraper
async def scrape_jiji_prices(brand: str, model: str) -> List[PriceData]:
    prices = []
    try:
        search_query = f"{brand}+{model}".lower()
        url = f"https://jiji.ng/mobile-phones?query={search_query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                listings = soup.find_all('div', {'data-cy': 'adcard'})
                for listing in listings[:5]:
                    try:
                        price_elem = listing.find('div', {'data-cy': 'adcard-price'})
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group())
                                if price > 10000:
                                    prices.append(PriceData(source="marketplace", price=price, currency="NGN"))
                    except:
                        continue
    except Exception as e:
        logging.error(f"Scraping error: {e}")
    return prices

# AI Price Estimation
async def estimate_price_with_ai(
    brand: str,
    model: str,
    condition: PhoneConditionExtended,
    new_price: Optional[float],
    used_price: Optional[float]
) -> dict:
    if not EMERGENT_LLM_KEY:
        return calculate_fallback_estimate(brand, model, new_price, used_price, condition)
    
    try:
        from emergentintegrations.llm.openai import LlmChat
        
        # For unknown phones, estimate base price from brand
        if not new_price and not used_price:
            # Get average price for brand
            brand_prices = REFERENCE_PRICES.get(brand, {})
            if brand_prices:
                avg_new = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
                avg_used = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
                new_price = avg_new
                used_price = avg_used
            else:
                # Default estimate for unknown brands
                new_price = 200000
                used_price = 80000
        
        new_price_str = f"₦{new_price:,.0f}" if new_price else "₦200,000 (estimated)"
        used_price_str = f"₦{used_price:,.0f}" if used_price else "₦80,000 (estimated)"
        
        condition_details = f"""
CONDITION:
- Screen: {condition.screen_condition}
- Body: {condition.body_condition}
- Battery: {condition.battery_health}
- Speakers: {condition.speakers_working}
- Cameras: {condition.cameras_working}
- Buttons: {condition.buttons_working}
- Network: {condition.network_status}
- Original Parts: {condition.original_parts}"""

        if is_iphone(brand):
            biometric_type = get_iphone_biometric_type(model)
            if biometric_type == "face_id":
                condition_details += f"\n- Face ID: {condition.face_id_working or 'yes'}"
            else:
                condition_details += f"\n- Touch ID: {condition.touch_id_working or 'yes'}"
            condition_details += f"""
- iCloud: {condition.icloud_status or 'unlocked'}
- Back Glass: {condition.back_glass_condition or 'intact'}
- True Tone: {condition.true_tone_working or 'yes'}"""
        else:
            condition_details += f"""
- Fingerprint: {condition.fingerprint_working or 'yes'}
- Face Unlock: {condition.face_unlock_working or 'yes'}
- FRP: {condition.frp_status or 'unlocked'}
- Charging Port: {condition.charging_port or 'excellent'}"""

        prompt = f"""You are a Nigerian phone valuation expert. Estimate the RESELLER BUYING PRICE.

PHONE: {brand} {model}
NEW PRICE: {new_price_str}
USED MARKET: {used_price_str}

{condition_details}

RULES:
- Resellers need 20-30% profit margin
- iCloud locked = 90% value loss
- FRP locked = 70% value loss
- Cracked screen = 40-50% loss
- Poor battery = 25-35% loss

Return JSON only:
{{"estimated_price": number, "confidence": "high/medium/low", "reasoning": "2-3 sentences"}}"""

        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"price_{uuid.uuid4()}",
            system_message="You are a conservative phone valuation expert in Nigeria."
        )
        response = await llm_chat.send_message(prompt)
        
        try:
            response_text = str(response.content if hasattr(response, 'content') else response).strip()
            if "```" in response_text:
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            result = json.loads(response_text)
            return {
                "estimated_price": float(result.get("estimated_price", 0)),
                "confidence": result.get("confidence", "medium"),
                "reasoning": result.get("reasoning", "AI estimation based on condition.")
            }
        except:
            return calculate_fallback_estimate(brand, model, new_price, used_price, condition)
            
    except Exception as e:
        logging.error(f"AI error: {e}")
        return calculate_fallback_estimate(brand, model, new_price, used_price, condition)

def calculate_fallback_estimate(
    brand: str,
    model: str,
    new_price: Optional[float],
    used_price: Optional[float],
    condition: PhoneConditionExtended
) -> dict:
    # For unknown phones, estimate based on brand average
    if not new_price and not used_price:
        brand_prices = REFERENCE_PRICES.get(brand, {})
        if brand_prices:
            new_price = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
            used_price = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
        else:
            new_price = 200000
            used_price = 80000
    
    screen_mult = {"excellent": 1.0, "good": 0.88, "fair": 0.65, "cracked": 0.45}.get(condition.screen_condition, 0.7)
    body_mult = {"excellent": 1.0, "good": 0.92, "fair": 0.8, "damaged": 0.55}.get(condition.body_condition, 0.8)
    battery_mult = {"excellent": 1.0, "good": 0.88, "fair": 0.72, "poor": 0.55}.get(condition.battery_health, 0.8)
    speakers_mult = {"yes": 1.0, "partial": 0.88, "no": 0.75}.get(condition.speakers_working, 0.9)
    cameras_mult = {"all_working": 1.0, "front_only": 0.8, "back_only": 0.8, "issues": 0.65}.get(condition.cameras_working, 0.85)
    buttons_mult = {"all_working": 1.0, "some_issues": 0.88, "major_issues": 0.7}.get(condition.buttons_working, 0.9)
    network_mult = {"unlocked": 1.0, "locked_to_carrier": 0.8}.get(condition.network_status, 0.9)
    parts_mult = {"yes": 1.0, "some_replaced": 0.85, "mostly_replaced": 0.65}.get(condition.original_parts, 0.85)
    
    if is_iphone(brand):
        biometric_type = get_iphone_biometric_type(model)
        if biometric_type == "face_id":
            bio_mult = {"yes": 1.0, "no": 0.6}.get(condition.face_id_working or "yes", 1.0)
        else:
            bio_mult = {"yes": 1.0, "no": 0.65}.get(condition.touch_id_working or "yes", 1.0)
        
        icloud_mult = {"unlocked": 1.0, "locked": 0.1}.get(condition.icloud_status or "unlocked", 1.0)
        backglass_mult = {"intact": 1.0, "cracked": 0.8}.get(condition.back_glass_condition or "intact", 1.0)
        truetone_mult = {"yes": 1.0, "no": 0.92}.get(condition.true_tone_working or "yes", 1.0)
        
        overall = (screen_mult + body_mult + battery_mult + speakers_mult + cameras_mult + 
                   buttons_mult + network_mult + parts_mult + bio_mult + icloud_mult + 
                   backglass_mult + truetone_mult) / 12
    else:
        fingerprint_mult = {"yes": 1.0, "no": 0.85, "not_applicable": 1.0}.get(condition.fingerprint_working or "yes", 1.0)
        face_mult = {"yes": 1.0, "no": 0.92, "not_applicable": 1.0}.get(condition.face_unlock_working or "yes", 1.0)
        frp_mult = {"unlocked": 1.0, "locked": 0.3}.get(condition.frp_status or "unlocked", 1.0)
        charging_mult = {"excellent": 1.0, "good": 0.92, "loose": 0.8, "damaged": 0.6}.get(condition.charging_port or "excellent", 1.0)
        
        overall = (screen_mult + body_mult + battery_mult + speakers_mult + cameras_mult + 
                   buttons_mult + network_mult + parts_mult + fingerprint_mult + face_mult +
                   frp_mult + charging_mult) / 12
    
    base_price = used_price if used_price else (new_price * 0.45 if new_price else 80000)
    estimated_price = base_price * overall
    
    return {
        "estimated_price": round(estimated_price, -3),
        "confidence": "medium" if new_price or used_price else "low",
        "reasoning": f"Based on condition score ({overall:.0%}). Price reflects reseller buying rate with repair costs."
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stashorra API - Phone Price Estimator"}

@api_router.get("/payment-info")
async def get_payment_info():
    """Get payment information for users"""
    return PAYMENT_INFO

@api_router.post("/verify-code")
async def verify_code(request: AccessCodeVerify):
    """Verify an access code"""
    result = await verify_access_code(request.code)
    return result

@api_router.get("/brands")
async def get_brands():
    return {"brands": ALL_BRANDS}

@api_router.get("/popular-phones")
async def get_popular_phones():
    brands = []
    for brand_name in ALL_BRANDS:
        models = list(REFERENCE_PRICES.get(brand_name, {}).keys())
        brand_type = "iphone" if brand_name == "Apple" else "android"
        brands.append({
            "name": brand_name,
            "models": models,
            "type": brand_type,
            "has_models": len(models) > 0
        })
    return {"brands": brands}

@api_router.get("/condition-questions/{brand}/{model}")
async def get_condition_questions_for_model(brand: str, model: str):
    common_questions = [
        {"id": "screen_condition", "label": "Screen Condition", "description": "Check for cracks, scratches, dead pixels",
         "options": [{"value": "excellent", "label": "Excellent", "desc": "Perfect display"},
                     {"value": "good", "label": "Good", "desc": "Minor scratches"},
                     {"value": "fair", "label": "Fair", "desc": "Visible scratches"},
                     {"value": "cracked", "label": "Cracked", "desc": "Cracked screen"}]},
        {"id": "body_condition", "label": "Body Condition", "description": "Check for dents, chips",
         "options": [{"value": "excellent", "label": "Excellent", "desc": "Like new"},
                     {"value": "good", "label": "Good", "desc": "Minor scuffs"},
                     {"value": "fair", "label": "Fair", "desc": "Visible dents"},
                     {"value": "damaged", "label": "Damaged", "desc": "Significant damage"}]},
        {"id": "battery_health", "label": "Battery Health", "description": "Check in settings",
         "options": [{"value": "excellent", "label": "90-100%", "desc": "Excellent"},
                     {"value": "good", "label": "80-89%", "desc": "Good"},
                     {"value": "fair", "label": "70-79%", "desc": "Fair"},
                     {"value": "poor", "label": "<70%", "desc": "Poor"}]},
        {"id": "speakers_working", "label": "Speakers", "description": "Test audio",
         "options": [{"value": "yes", "label": "Working", "desc": "Clear sound"},
                     {"value": "partial", "label": "Partial", "desc": "Some issues"},
                     {"value": "no", "label": "Not Working", "desc": "Major issues"}]},
        {"id": "cameras_working", "label": "Cameras", "description": "Test all cameras",
         "options": [{"value": "all_working", "label": "All Working", "desc": "Perfect"},
                     {"value": "front_only", "label": "Front Only", "desc": "Back issues"},
                     {"value": "back_only", "label": "Back Only", "desc": "Front issues"},
                     {"value": "issues", "label": "Major Issues", "desc": "Both have problems"}]},
        {"id": "buttons_working", "label": "Buttons", "description": "Test all buttons",
         "options": [{"value": "all_working", "label": "All Working", "desc": "Responsive"},
                     {"value": "some_issues", "label": "Some Issues", "desc": "Some sticky"},
                     {"value": "major_issues", "label": "Major Issues", "desc": "Not working"}]},
        {"id": "network_status", "label": "Network Lock", "description": "Is it unlocked?",
         "options": [{"value": "unlocked", "label": "Unlocked", "desc": "Any SIM"},
                     {"value": "locked_to_carrier", "label": "Locked", "desc": "Specific carrier"}]},
        {"id": "original_parts", "label": "Original Parts", "description": "All original?",
         "options": [{"value": "yes", "label": "All Original", "desc": "No replacements"},
                     {"value": "some_replaced", "label": "Some Replaced", "desc": "Screen/battery"},
                     {"value": "mostly_replaced", "label": "Mostly Replaced", "desc": "Multiple parts"}]}
    ]
    
    if is_iphone(brand):
        biometric_type = get_iphone_biometric_type(model)
        iphone_questions = []
        
        if biometric_type == "face_id":
            iphone_questions.append({"id": "face_id_working", "label": "Face ID", "description": "Test Face ID",
                "options": [{"value": "yes", "label": "Working", "desc": "Works perfectly"},
                           {"value": "no", "label": "Not Working", "desc": "Broken"}]})
        else:
            iphone_questions.append({"id": "touch_id_working", "label": "Touch ID", "description": "Test Touch ID",
                "options": [{"value": "yes", "label": "Working", "desc": "Works perfectly"},
                           {"value": "no", "label": "Not Working", "desc": "Broken"}]})
        
        iphone_questions.extend([
            {"id": "icloud_status", "label": "iCloud Status", "description": "CRITICAL: Is iCloud signed out?",
             "options": [{"value": "unlocked", "label": "Unlocked", "desc": "No iCloud linked"},
                        {"value": "locked", "label": "Locked", "desc": "Previous owner's account"}]},
            {"id": "back_glass_condition", "label": "Back Glass", "description": "Check back panel",
             "options": [{"value": "intact", "label": "Intact", "desc": "No cracks"},
                        {"value": "cracked", "label": "Cracked", "desc": "Cracked"}]},
            {"id": "true_tone_working", "label": "True Tone", "description": "Available in settings?",
             "options": [{"value": "yes", "label": "Working", "desc": "Available"},
                        {"value": "no", "label": "Not Working", "desc": "Disabled"}]}
        ])
        return {"questions": common_questions + iphone_questions, "biometric_type": biometric_type}
    else:
        android_questions = [
            {"id": "fingerprint_working", "label": "Fingerprint", "description": "Test sensor",
             "options": [{"value": "yes", "label": "Working", "desc": "Works"},
                        {"value": "no", "label": "Not Working", "desc": "Broken"},
                        {"value": "not_applicable", "label": "N/A", "desc": "No sensor"}]},
            {"id": "face_unlock_working", "label": "Face Unlock", "description": "Test face unlock",
             "options": [{"value": "yes", "label": "Working", "desc": "Works"},
                        {"value": "no", "label": "Not Working", "desc": "Broken"},
                        {"value": "not_applicable", "label": "N/A", "desc": "Not available"}]},
            {"id": "frp_status", "label": "FRP Status", "description": "CRITICAL: Google account removed?",
             "options": [{"value": "unlocked", "label": "Unlocked", "desc": "No Google lock"},
                        {"value": "locked", "label": "Locked", "desc": "Previous account"}]},
            {"id": "charging_port", "label": "Charging Port", "description": "Test charging",
             "options": [{"value": "excellent", "label": "Excellent", "desc": "Perfect"},
                        {"value": "good", "label": "Good", "desc": "Minor wear"},
                        {"value": "loose", "label": "Loose", "desc": "Doesn't hold"},
                        {"value": "damaged", "label": "Damaged", "desc": "Issues"}]}
        ]
        return {"questions": common_questions + android_questions, "biometric_type": "fingerprint"}

@api_router.post("/search-phone", response_model=ScrapedPrices)
async def search_phone_prices(request: PhoneSearchRequest):
    jiji_prices = await scrape_jiji_prices(request.brand, request.model)
    ref_prices = get_reference_prices(request.brand, request.model)
    
    new_prices = []
    used_prices = jiji_prices if jiji_prices else []
    
    # If we have reference prices, use them
    if ref_prices["new"]:
        new_prices = [PriceData(source="market", price=ref_prices["new"], currency="NGN")]
    
    if not used_prices and ref_prices["used"]:
        used_prices = [PriceData(source="market", price=ref_prices["used"], currency="NGN")]
    
    # For unknown phones, estimate from brand average
    if not new_prices and not used_prices:
        brand_prices = REFERENCE_PRICES.get(request.brand, {})
        if brand_prices:
            avg_new = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
            avg_used = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
            new_prices = [PriceData(source="estimated", price=avg_new, currency="NGN")]
            used_prices = [PriceData(source="estimated", price=avg_used, currency="NGN")]
        else:
            # Default for unknown brands
            new_prices = [PriceData(source="estimated", price=200000, currency="NGN")]
            used_prices = [PriceData(source="estimated", price=80000, currency="NGN")]
    
    return ScrapedPrices(new_prices=new_prices, used_prices=used_prices)

@api_router.post("/estimate-price", response_model=PriceEstimate)
async def estimate_price(request: PriceEstimateRequest):
    # Verify access code
    code_check = await verify_access_code(request.access_code)
    if not code_check["valid"]:
        raise HTTPException(status_code=403, detail=code_check["message"])
    
    # Use one credit
    used = await use_access_code(request.access_code)
    if not used:
        raise HTTPException(status_code=403, detail="Failed to use access code. Please try again.")
    
    ai_result = await estimate_price_with_ai(
        brand=request.brand,
        model=request.model,
        condition=request.condition,
        new_price=request.new_price,
        used_price=request.used_price
    )
    
    estimate = PriceEstimate(
        brand=request.brand,
        model=request.model,
        condition=request.condition.model_dump(),
        new_price_avg=request.new_price,
        used_price_avg=request.used_price,
        estimated_price=ai_result["estimated_price"],
        confidence=ai_result["confidence"],
        reasoning=ai_result["reasoning"]
    )
    
    doc = estimate.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    doc['access_code'] = request.access_code.upper()
    await db.estimates.insert_one(doc)
    
    return estimate

@api_router.get("/estimates")
async def get_estimates(limit: int = 10):
    estimates = await db.estimates.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return estimates

# Admin Routes
class AdminGenerateCode(BaseModel):
    username: str
    password: str
    note: Optional[str] = None

@api_router.post("/admin/login")
async def admin_login(request: AdminLogin):
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/admin/generate-code")
async def generate_code(request: AdminGenerateCode):
    # Verify admin
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    code = generate_access_code()
    
    # Ensure unique code
    while await db.access_codes.find_one({"code": code}):
        code = generate_access_code()
    
    access_code_doc = {
        "code": code,
        "uses_remaining": PAYMENT_INFO["uses_per_payment"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": request.note or "",
        "last_used": None
    }
    
    await db.access_codes.insert_one(access_code_doc)
    
    return {
        "code": code,
        "uses": PAYMENT_INFO["uses_per_payment"],
        "created_at": access_code_doc["created_at"]
    }

@api_router.get("/admin/codes")
async def get_all_codes(username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    codes = await db.access_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"codes": codes}

@api_router.delete("/admin/code/{code}")
async def delete_code(code: str, username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    result = await db.access_codes.delete_one({"code": code.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Code not found")
    
    return {"message": "Code deleted"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
