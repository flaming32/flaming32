from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
import re
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI setup via Emergent
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

app = FastAPI()
api_router = APIRouter(prefix="/api")

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

# iPhone biometric info - which models have Face ID vs Touch ID
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

# Reference prices - SIGNIFICANTLY LOWERED for realistic used market values
# Used prices are what a reseller would pay (lower because they need profit margin)
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
        "Note 30 VIP": {"new": 280000, "used": 110000},
        "Hot 40 Pro": {"new": 180000, "used": 65000},
        "Hot 40": {"new": 140000, "used": 50000},
        "Hot 40i": {"new": 110000, "used": 38000},
        "Hot 30": {"new": 120000, "used": 42000},
        "Hot 30i": {"new": 90000, "used": 30000},
        "Smart 8": {"new": 95000, "used": 32000},
        "Smart 8 Plus": {"new": 110000, "used": 38000},
        "Smart 7": {"new": 75000, "used": 25000},
        "GT 20 Pro": {"new": 400000, "used": 160000},
    },
    "Itel": {
        "S24": {"new": 130000, "used": 45000},
        "S23+": {"new": 110000, "used": 38000},
        "S23": {"new": 90000, "used": 30000},
        "P55+": {"new": 100000, "used": 35000},
        "P55": {"new": 80000, "used": 28000},
        "P40+": {"new": 70000, "used": 24000},
        "P40": {"new": 55000, "used": 18000},
        "A70": {"new": 85000, "used": 28000},
        "A60": {"new": 65000, "used": 22000},
        "A60s": {"new": 60000, "used": 20000},
        "A50": {"new": 50000, "used": 16000},
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
        "Note 12 Pro+": {"new": 320000, "used": 120000},
        "Note 12 Pro": {"new": 260000, "used": 95000},
        "Note 12": {"new": 180000, "used": 65000},
        "13C": {"new": 130000, "used": 45000},
        "12": {"new": 150000, "used": 52000},
        "A3": {"new": 85000, "used": 28000},
    },
    "Poco": {
        "X6 Pro": {"new": 450000, "used": 180000},
        "X6": {"new": 350000, "used": 140000},
        "X5 Pro": {"new": 320000, "used": 120000},
        "M6 Pro": {"new": 200000, "used": 75000},
        "C65": {"new": 120000, "used": 42000},
    },
    "Google": {
        "Pixel 8 Pro": {"new": 1100000, "used": 480000},
        "Pixel 8": {"new": 800000, "used": 320000},
        "Pixel 8a": {"new": 600000, "used": 240000},
        "Pixel 7 Pro": {"new": 750000, "used": 280000},
        "Pixel 7": {"new": 550000, "used": 200000},
        "Pixel 7a": {"new": 450000, "used": 170000},
        "Pixel 6 Pro": {"new": 550000, "used": 190000},
        "Pixel 6": {"new": 420000, "used": 150000},
        "Pixel 6a": {"new": 350000, "used": 120000},
    },
    "OnePlus": {
        "12": {"new": 1200000, "used": 520000},
        "12R": {"new": 800000, "used": 320000},
        "11": {"new": 900000, "used": 340000},
        "11R": {"new": 650000, "used": 250000},
        "Nord 3": {"new": 450000, "used": 170000},
        "Nord CE 3": {"new": 350000, "used": 130000},
        "Nord N30": {"new": 280000, "used": 100000},
    },
    "Oppo": {
        "Find X7 Ultra": {"new": 1500000, "used": 650000},
        "Find X6 Pro": {"new": 1100000, "used": 450000},
        "Reno 11 Pro": {"new": 650000, "used": 260000},
        "Reno 11": {"new": 480000, "used": 180000},
        "Reno 10 Pro+": {"new": 550000, "used": 210000},
        "Reno 10 Pro": {"new": 450000, "used": 170000},
        "Reno 10": {"new": 350000, "used": 130000},
        "A98": {"new": 320000, "used": 120000},
        "A78": {"new": 250000, "used": 90000},
        "A58": {"new": 180000, "used": 65000},
        "A18": {"new": 130000, "used": 45000},
    },
    "Vivo": {
        "X100 Pro": {"new": 1300000, "used": 550000},
        "X100": {"new": 950000, "used": 380000},
        "V30 Pro": {"new": 650000, "used": 260000},
        "V30": {"new": 500000, "used": 190000},
        "V29": {"new": 450000, "used": 170000},
        "Y100": {"new": 280000, "used": 105000},
        "Y36": {"new": 180000, "used": 65000},
        "Y27": {"new": 150000, "used": 52000},
    },
    "Realme": {
        "GT 5 Pro": {"new": 800000, "used": 320000},
        "GT Neo 5": {"new": 550000, "used": 210000},
        "12 Pro+": {"new": 500000, "used": 190000},
        "12 Pro": {"new": 400000, "used": 150000},
        "12": {"new": 280000, "used": 105000},
        "C67": {"new": 180000, "used": 65000},
        "C55": {"new": 150000, "used": 52000},
        "C53": {"new": 130000, "used": 45000},
        "Note 50": {"new": 100000, "used": 35000},
    },
    "Huawei": {
        "Mate 60 Pro": {"new": 1500000, "used": 650000},
        "Mate 60": {"new": 1200000, "used": 500000},
        "P60 Pro": {"new": 1100000, "used": 450000},
        "P60": {"new": 900000, "used": 360000},
        "Nova 12 Pro": {"new": 550000, "used": 210000},
        "Nova 12": {"new": 400000, "used": 150000},
        "Nova 11 Pro": {"new": 450000, "used": 170000},
        "Nova 11": {"new": 350000, "used": 130000},
    },
    "Honor": {
        "Magic 6 Pro": {"new": 1200000, "used": 500000},
        "Magic 6": {"new": 900000, "used": 360000},
        "90 Pro": {"new": 650000, "used": 250000},
        "90": {"new": 480000, "used": 180000},
        "X9b": {"new": 350000, "used": 130000},
        "X8b": {"new": 280000, "used": 100000},
    },
    "Nokia": {
        "G42": {"new": 200000, "used": 70000},
        "G22": {"new": 150000, "used": 52000},
        "C32": {"new": 100000, "used": 35000},
        "C22": {"new": 80000, "used": 28000},
        "C12": {"new": 60000, "used": 20000},
    },
    "Motorola": {
        "Edge 40 Pro": {"new": 750000, "used": 300000},
        "Edge 40": {"new": 550000, "used": 210000},
        "G84": {"new": 350000, "used": 130000},
        "G54": {"new": 250000, "used": 90000},
        "G34": {"new": 180000, "used": 65000},
        "E13": {"new": 100000, "used": 35000},
    },
    "Sony": {
        "Xperia 1 V": {"new": 1400000, "used": 600000},
        "Xperia 5 V": {"new": 1000000, "used": 400000},
        "Xperia 10 V": {"new": 550000, "used": 210000},
    },
    "Asus": {
        "ROG Phone 8 Pro": {"new": 1500000, "used": 650000},
        "ROG Phone 8": {"new": 1200000, "used": 500000},
        "Zenfone 10": {"new": 900000, "used": 360000},
    },
}

def is_iphone(brand: str) -> bool:
    return brand.lower() == "apple"

def get_iphone_biometric_type(model: str) -> str:
    """Determine if iPhone uses Face ID or Touch ID"""
    if model in IPHONE_FACE_ID_MODELS:
        return "face_id"
    elif model in IPHONE_TOUCH_ID_MODELS:
        return "touch_id"
    else:
        # Default to Face ID for newer unknown models
        return "face_id"

def get_reference_prices(brand: str, model: str) -> dict:
    brand_prices = REFERENCE_PRICES.get(brand, {})
    return brand_prices.get(model, {"new": None, "used": None})

# Web Scraper Functions
async def scrape_jiji_prices(brand: str, model: str) -> List[PriceData]:
    prices = []
    search_query = f"{brand}+{model}".lower()
    url = f"https://jiji.ng/mobile-phones?query={search_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                listings = soup.find_all('div', {'data-cy': 'adcard'})
                
                for listing in listings[:10]:
                    try:
                        title_elem = listing.find('div', {'data-cy': 'adcard-title'})
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        price_elem = listing.find('div', {'data-cy': 'adcard-price'})
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group().replace(',', ''))
                                if title and price > 10000:
                                    prices.append(PriceData(
                                        source="marketplace",
                                        price=price,
                                        currency="NGN",
                                        title=title
                                    ))
                    except Exception:
                        continue
    except Exception as e:
        logging.error(f"Scraping error: {e}")
    
    return prices

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
        
        new_price_str = f"₦{new_price:,.0f}" if new_price else "Unknown"
        used_price_str = f"₦{used_price:,.0f}" if used_price else "Unknown"
        
        condition_details = f"""
BASIC CONDITION:
- Screen: {condition.screen_condition}
- Body/Frame: {condition.body_condition}
- Battery Health: {condition.battery_health}
- Speakers: {condition.speakers_working}
- Cameras: {condition.cameras_working}
- Buttons: {condition.buttons_working}
- Network: {condition.network_status}
- Original Parts: {condition.original_parts}"""

        if is_iphone(brand):
            biometric_type = get_iphone_biometric_type(model)
            if biometric_type == "face_id":
                condition_details += f"\n- Face ID: {condition.face_id_working or 'N/A'}"
            else:
                condition_details += f"\n- Touch ID: {condition.touch_id_working or 'N/A'}"
            condition_details += f"""
- iCloud Status: {condition.icloud_status or 'N/A'}
- Back Glass: {condition.back_glass_condition or 'N/A'}
- True Tone: {condition.true_tone_working or 'N/A'}"""
        else:
            condition_details += f"""
- Fingerprint: {condition.fingerprint_working or 'N/A'}
- Face Unlock: {condition.face_unlock_working or 'N/A'}
- FRP Status: {condition.frp_status or 'N/A'}
- Charging Port: {condition.charging_port or 'N/A'}"""

        prompt = f"""You are an expert phone valuation specialist in Nigeria. Estimate the RESELLER BUYING PRICE for a used phone.

PHONE: {brand} {model}
NEW RETAIL PRICE: {new_price_str}
MARKET USED PRICE: {used_price_str}

{condition_details}

CRITICAL VALUATION RULES:
1. This is what a RESELLER would pay - they need 20-30% profit margin
2. Used phones should be 40-60% of new price MAX in good condition
3. iCloud locked iPhones = nearly worthless (90% value loss)
4. FRP locked Androids = major value loss (70% loss)
5. Cracked screens = 40-50% value reduction
6. Poor battery = 25-35% reduction
7. Non-working biometrics = 30-40% reduction
8. Non-original parts = 20-30% reduction

The buyer needs to fix issues and make profit. Be CONSERVATIVE with pricing.

JSON response only:
{{"estimated_price": number, "confidence": "high/medium/low", "reasoning": "2-3 sentences"}}"""

        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"price_{uuid.uuid4()}",
            system_message="You are a conservative phone valuation expert."
        )
        response = await llm_chat.send_message(prompt)
        
        try:
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            response_text = response_text.strip()
            if "```" in response_text:
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            result = json.loads(response_text)
            return {
                "estimated_price": float(result.get("estimated_price", 0)),
                "confidence": result.get("confidence", "medium"),
                "reasoning": result.get("reasoning", "AI estimation based on condition.")
            }
        except Exception as e:
            logging.error(f"Parse error: {e}")
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
    # Base multipliers - MORE CONSERVATIVE
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
            bio_mult = {"yes": 1.0, "no": 0.6, "not_applicable": 1.0}.get(condition.face_id_working or "yes", 1.0)
        else:
            bio_mult = {"yes": 1.0, "no": 0.65, "not_applicable": 1.0}.get(condition.touch_id_working or "yes", 1.0)
        
        icloud_mult = {"unlocked": 1.0, "locked": 0.1}.get(condition.icloud_status or "unlocked", 1.0)
        backglass_mult = {"intact": 1.0, "cracked": 0.8, "not_applicable": 1.0}.get(condition.back_glass_condition or "intact", 1.0)
        truetone_mult = {"yes": 1.0, "no": 0.92, "not_applicable": 1.0}.get(condition.true_tone_working or "yes", 1.0)
        
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
    
    # Use the USED price as base, not new price
    if used_price:
        base_price = used_price
    elif new_price:
        base_price = new_price * 0.45  # Used is about 45% of new for reseller
    else:
        base_price = 0
    
    estimated_price = base_price * overall
    
    confidence = "high" if new_price and used_price else ("medium" if new_price or used_price else "low")
    
    return {
        "estimated_price": round(estimated_price, -3),  # Round to nearest 1000
        "confidence": confidence,
        "reasoning": f"Based on condition score ({overall:.0%}). Price reflects reseller buying rate with repair costs considered."
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stashorra API - Phone Price Estimator"}

@api_router.get("/brands")
async def get_brands():
    """Get all available brands alphabetically sorted"""
    return {"brands": ALL_BRANDS}

@api_router.get("/popular-phones")
async def get_popular_phones():
    """Get brands with known models"""
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
    """Get condition questions based on phone brand AND model"""
    
    common_questions = [
        {
            "id": "screen_condition",
            "label": "Screen Condition",
            "description": "Check for cracks, scratches, dead pixels, burn-in",
            "options": [
                {"value": "excellent", "label": "Excellent", "desc": "No scratches, perfect display"},
                {"value": "good", "label": "Good", "desc": "Minor scratches, not visible when on"},
                {"value": "fair", "label": "Fair", "desc": "Visible scratches or minor issues"},
                {"value": "cracked", "label": "Cracked", "desc": "Cracked or shattered"}
            ]
        },
        {
            "id": "body_condition",
            "label": "Body/Frame Condition",
            "description": "Inspect all sides for dents, chips, damage",
            "options": [
                {"value": "excellent", "label": "Excellent", "desc": "Like new, no visible wear"},
                {"value": "good", "label": "Good", "desc": "Minor scuffs or scratches"},
                {"value": "fair", "label": "Fair", "desc": "Noticeable dents or scratches"},
                {"value": "damaged", "label": "Damaged", "desc": "Significant damage"}
            ]
        },
        {
            "id": "battery_health",
            "label": "Battery Health",
            "description": "Check battery health in settings",
            "options": [
                {"value": "excellent", "label": "Excellent (90-100%)", "desc": "Holds charge all day"},
                {"value": "good", "label": "Good (80-89%)", "desc": "Good battery life"},
                {"value": "fair", "label": "Fair (70-79%)", "desc": "Needs frequent charging"},
                {"value": "poor", "label": "Poor (<70%)", "desc": "Very poor battery"}
            ]
        },
        {
            "id": "speakers_working",
            "label": "Speakers & Earpiece",
            "description": "Test audio playback and call quality",
            "options": [
                {"value": "yes", "label": "All Working", "desc": "Clear sound"},
                {"value": "partial", "label": "Partial Issues", "desc": "Some crackling"},
                {"value": "no", "label": "Not Working", "desc": "Major audio issues"}
            ]
        },
        {
            "id": "cameras_working",
            "label": "Cameras",
            "description": "Test front and back cameras",
            "options": [
                {"value": "all_working", "label": "All Working", "desc": "Perfect focus and quality"},
                {"value": "front_only", "label": "Front Only", "desc": "Back camera issues"},
                {"value": "back_only", "label": "Back Only", "desc": "Front camera issues"},
                {"value": "issues", "label": "Major Issues", "desc": "Both have problems"}
            ]
        },
        {
            "id": "buttons_working",
            "label": "Physical Buttons",
            "description": "Test power, volume buttons",
            "options": [
                {"value": "all_working", "label": "All Working", "desc": "All buttons respond"},
                {"value": "some_issues", "label": "Some Issues", "desc": "Some sticky/unresponsive"},
                {"value": "major_issues", "label": "Major Issues", "desc": "Multiple not working"}
            ]
        },
        {
            "id": "network_status",
            "label": "Network Lock",
            "description": "Is the phone unlocked?",
            "options": [
                {"value": "unlocked", "label": "Unlocked", "desc": "Works with any SIM"},
                {"value": "locked_to_carrier", "label": "Carrier Locked", "desc": "Only specific carrier"}
            ]
        },
        {
            "id": "original_parts",
            "label": "Original Parts",
            "description": "Are all parts original?",
            "options": [
                {"value": "yes", "label": "All Original", "desc": "No replacements"},
                {"value": "some_replaced", "label": "Some Replaced", "desc": "Screen or battery replaced"},
                {"value": "mostly_replaced", "label": "Mostly Replaced", "desc": "Multiple non-original"}
            ]
        }
    ]
    
    if is_iphone(brand):
        biometric_type = get_iphone_biometric_type(model)
        iphone_questions = []
        
        if biometric_type == "face_id":
            iphone_questions.append({
                "id": "face_id_working",
                "label": "Face ID",
                "description": "Test Face ID unlock",
                "options": [
                    {"value": "yes", "label": "Working", "desc": "Face ID works perfectly"},
                    {"value": "no", "label": "Not Working", "desc": "Face ID disabled/broken"}
                ]
            })
        else:
            iphone_questions.append({
                "id": "touch_id_working",
                "label": "Touch ID",
                "description": "Test fingerprint sensor",
                "options": [
                    {"value": "yes", "label": "Working", "desc": "Touch ID works"},
                    {"value": "no", "label": "Not Working", "desc": "Touch ID not responding"}
                ]
            })
        
        iphone_questions.extend([
            {
                "id": "icloud_status",
                "label": "iCloud Lock Status",
                "description": "CRITICAL: Is iCloud signed out?",
                "options": [
                    {"value": "unlocked", "label": "Unlocked/Signed Out", "desc": "No iCloud linked"},
                    {"value": "locked", "label": "iCloud Locked", "desc": "Previous owner's account"}
                ]
            },
            {
                "id": "back_glass_condition",
                "label": "Back Glass",
                "description": "Check back glass panel",
                "options": [
                    {"value": "intact", "label": "Intact", "desc": "No cracks"},
                    {"value": "cracked", "label": "Cracked", "desc": "Back glass cracked"}
                ]
            },
            {
                "id": "true_tone_working",
                "label": "True Tone Display",
                "description": "Is True Tone available in settings?",
                "options": [
                    {"value": "yes", "label": "Working", "desc": "True Tone available"},
                    {"value": "no", "label": "Not Working", "desc": "True Tone disabled"}
                ]
            }
        ])
        
        return {"questions": common_questions + iphone_questions, "biometric_type": biometric_type}
    else:
        android_questions = [
            {
                "id": "fingerprint_working",
                "label": "Fingerprint Sensor",
                "description": "Test fingerprint scanner",
                "options": [
                    {"value": "yes", "label": "Working", "desc": "Works perfectly"},
                    {"value": "no", "label": "Not Working", "desc": "Not responding"},
                    {"value": "not_applicable", "label": "N/A", "desc": "No fingerprint sensor"}
                ]
            },
            {
                "id": "face_unlock_working",
                "label": "Face Unlock",
                "description": "Test face unlock feature",
                "options": [
                    {"value": "yes", "label": "Working", "desc": "Works perfectly"},
                    {"value": "no", "label": "Not Working", "desc": "Not available"},
                    {"value": "not_applicable", "label": "N/A", "desc": "No face unlock"}
                ]
            },
            {
                "id": "frp_status",
                "label": "FRP (Google Lock)",
                "description": "CRITICAL: Is Google account removed?",
                "options": [
                    {"value": "unlocked", "label": "Unlocked", "desc": "No Google account"},
                    {"value": "locked", "label": "FRP Locked", "desc": "Previous Google account"}
                ]
            },
            {
                "id": "charging_port",
                "label": "Charging Port",
                "description": "Test charging connection",
                "options": [
                    {"value": "excellent", "label": "Excellent", "desc": "Tight fit, charges well"},
                    {"value": "good", "label": "Good", "desc": "Works, minor wear"},
                    {"value": "loose", "label": "Loose", "desc": "Cable doesn't hold"},
                    {"value": "damaged", "label": "Damaged", "desc": "Charging issues"}
                ]
            }
        ]
        
        return {"questions": common_questions + android_questions, "biometric_type": "fingerprint"}

@api_router.post("/search-phone", response_model=ScrapedPrices)
async def search_phone_prices(request: PhoneSearchRequest):
    jiji_prices = await scrape_jiji_prices(request.brand, request.model)
    ref_prices = get_reference_prices(request.brand, request.model)
    
    new_prices = []
    used_prices = jiji_prices if jiji_prices else []
    
    if ref_prices["new"]:
        new_prices = [PriceData(
            source="market_reference",
            price=ref_prices["new"],
            currency="NGN",
            title=f"{request.brand} {request.model} (New)"
        )]
    
    if not used_prices and ref_prices["used"]:
        used_prices = [PriceData(
            source="market_reference",
            price=ref_prices["used"],
            currency="NGN",
            title=f"{request.brand} {request.model} (Used)"
        )]
    
    return ScrapedPrices(new_prices=new_prices, used_prices=used_prices)

@api_router.post("/estimate-price", response_model=PriceEstimate)
async def estimate_price(request: PriceEstimateRequest):
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
    await db.estimates.insert_one(doc)
    
    return estimate

@api_router.get("/estimates", response_model=List[PriceEstimate])
async def get_estimates(limit: int = 10):
    estimates = await db.estimates.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    for est in estimates:
        if isinstance(est.get('timestamp'), str):
            est['timestamp'] = datetime.fromisoformat(est['timestamp'])
    return estimates

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
