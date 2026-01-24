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

# Models
class PhoneSearchRequest(BaseModel):
    brand: str
    model: str

class PhoneConditionExtended(BaseModel):
    # Common questions for all phones
    screen_condition: str  # excellent, good, fair, cracked
    body_condition: str    # excellent, good, fair, damaged
    battery_health: str    # excellent, good, fair, poor
    
    # iPhone specific
    face_id_working: Optional[str] = None      # yes, no, not_applicable
    touch_id_working: Optional[str] = None     # yes, no, not_applicable
    icloud_status: Optional[str] = None        # unlocked, locked, not_applicable
    back_glass_condition: Optional[str] = None # intact, cracked, not_applicable
    true_tone_working: Optional[str] = None    # yes, no, not_applicable
    
    # Android specific
    fingerprint_working: Optional[str] = None  # yes, no, not_applicable
    frp_status: Optional[str] = None           # unlocked, locked, not_applicable
    charging_port: Optional[str] = None        # excellent, good, loose, damaged
    
    # Common functionality
    speakers_working: str = "yes"              # yes, partial, no
    cameras_working: str = "yes"               # all_working, front_only, back_only, issues
    buttons_working: str = "yes"               # all_working, some_issues, major_issues
    network_status: str = "unlocked"           # unlocked, locked_to_carrier
    original_parts: str = "yes"                # yes, some_replaced, mostly_replaced

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

# Extended Reference prices for phones (in NGN)
REFERENCE_PRICES = {
    # Apple - prices from Jiji.ng used market
    "Apple": {
        "iPhone 15 Pro Max": {"new": 2200000, "used": 1450000},
        "iPhone 15 Pro": {"new": 1900000, "used": 1250000},
        "iPhone 15 Plus": {"new": 1500000, "used": 1000000},
        "iPhone 15": {"new": 1400000, "used": 900000},
        "iPhone 14 Pro Max": {"new": 1600000, "used": 950000},
        "iPhone 14 Pro": {"new": 1400000, "used": 800000},
        "iPhone 14 Plus": {"new": 1100000, "used": 700000},
        "iPhone 14": {"new": 1000000, "used": 650000},
        "iPhone 13 Pro Max": {"new": 1200000, "used": 680000},
        "iPhone 13 Pro": {"new": 1000000, "used": 580000},
        "iPhone 13": {"new": 750000, "used": 450000},
        "iPhone 13 Mini": {"new": 650000, "used": 380000},
        "iPhone 12 Pro Max": {"new": 850000, "used": 480000},
        "iPhone 12 Pro": {"new": 700000, "used": 400000},
        "iPhone 12": {"new": 550000, "used": 320000},
        "iPhone 12 Mini": {"new": 450000, "used": 250000},
        "iPhone 11 Pro Max": {"new": 650000, "used": 350000},
        "iPhone 11 Pro": {"new": 550000, "used": 300000},
        "iPhone 11": {"new": 420000, "used": 230000},
        "iPhone XS Max": {"new": 450000, "used": 220000},
        "iPhone XS": {"new": 380000, "used": 180000},
        "iPhone XR": {"new": 320000, "used": 160000},
        "iPhone X": {"new": 300000, "used": 150000},
        "iPhone SE (2022)": {"new": 450000, "used": 280000},
        "iPhone SE (2020)": {"new": 320000, "used": 180000},
    },
    # Samsung - Android flagship
    "Samsung": {
        "Galaxy S24 Ultra": {"new": 2100000, "used": 1400000},
        "Galaxy S24+": {"new": 1500000, "used": 1000000},
        "Galaxy S24": {"new": 1200000, "used": 800000},
        "Galaxy S23 Ultra": {"new": 1500000, "used": 900000},
        "Galaxy S23+": {"new": 1100000, "used": 700000},
        "Galaxy S23": {"new": 900000, "used": 550000},
        "Galaxy S22 Ultra": {"new": 1000000, "used": 580000},
        "Galaxy S22+": {"new": 750000, "used": 450000},
        "Galaxy S22": {"new": 600000, "used": 350000},
        "Galaxy S21 Ultra": {"new": 750000, "used": 400000},
        "Galaxy S21+": {"new": 550000, "used": 300000},
        "Galaxy S21": {"new": 450000, "used": 250000},
        "Galaxy Z Fold 5": {"new": 2800000, "used": 1900000},
        "Galaxy Z Fold 4": {"new": 2000000, "used": 1200000},
        "Galaxy Z Flip 5": {"new": 1300000, "used": 850000},
        "Galaxy Z Flip 4": {"new": 900000, "used": 550000},
        "Galaxy A54": {"new": 380000, "used": 250000},
        "Galaxy A34": {"new": 280000, "used": 180000},
        "Galaxy A24": {"new": 200000, "used": 130000},
        "Galaxy A14": {"new": 150000, "used": 95000},
        "Galaxy A04": {"new": 100000, "used": 65000},
        "Galaxy M54": {"new": 350000, "used": 230000},
        "Galaxy M34": {"new": 250000, "used": 160000},
    },
    # Tecno - Popular in Nigeria (Slot.ng prices)
    "Tecno": {
        "Phantom X2 Pro": {"new": 550000, "used": 350000},
        "Phantom X2": {"new": 450000, "used": 280000},
        "Phantom V Fold": {"new": 900000, "used": 600000},
        "Phantom V Flip": {"new": 550000, "used": 350000},
        "Camon 30 Pro": {"new": 350000, "used": 230000},
        "Camon 30": {"new": 280000, "used": 180000},
        "Camon 20 Pro": {"new": 280000, "used": 170000},
        "Camon 20": {"new": 180000, "used": 110000},
        "Camon 19 Pro": {"new": 200000, "used": 120000},
        "Camon 19": {"new": 150000, "used": 90000},
        "Spark 20 Pro+": {"new": 220000, "used": 140000},
        "Spark 20 Pro": {"new": 180000, "used": 110000},
        "Spark 20": {"new": 130000, "used": 80000},
        "Spark 10 Pro": {"new": 150000, "used": 90000},
        "Spark 10": {"new": 100000, "used": 60000},
        "Pova 6 Pro": {"new": 280000, "used": 180000},
        "Pova 6": {"new": 200000, "used": 130000},
        "Pova 5 Pro": {"new": 200000, "used": 120000},
        "Pova 5": {"new": 160000, "used": 100000},
        "Pop 8": {"new": 80000, "used": 50000},
        "Pop 7": {"new": 65000, "used": 40000},
    },
    # Infinix - Popular in Nigeria (Slot.ng prices)
    "Infinix": {
        "Zero 30": {"new": 350000, "used": 220000},
        "Zero 20": {"new": 280000, "used": 170000},
        "Note 40 Pro": {"new": 320000, "used": 200000},
        "Note 40": {"new": 250000, "used": 160000},
        "Note 30 Pro": {"new": 220000, "used": 140000},
        "Note 30": {"new": 170000, "used": 105000},
        "Note 30 VIP": {"new": 280000, "used": 180000},
        "Hot 40 Pro": {"new": 180000, "used": 110000},
        "Hot 40": {"new": 140000, "used": 85000},
        "Hot 40i": {"new": 110000, "used": 70000},
        "Hot 30": {"new": 120000, "used": 75000},
        "Hot 30i": {"new": 90000, "used": 55000},
        "Smart 8": {"new": 95000, "used": 60000},
        "Smart 8 Plus": {"new": 110000, "used": 70000},
        "Smart 7": {"new": 75000, "used": 45000},
        "GT 20 Pro": {"new": 400000, "used": 260000},
    },
    # Itel - Budget phones (Slot.ng prices)
    "Itel": {
        "S24": {"new": 130000, "used": 80000},
        "S23+": {"new": 110000, "used": 70000},
        "S23": {"new": 90000, "used": 55000},
        "P55+": {"new": 100000, "used": 65000},
        "P55": {"new": 80000, "used": 50000},
        "P40+": {"new": 70000, "used": 45000},
        "P40": {"new": 55000, "used": 35000},
        "A70": {"new": 85000, "used": 55000},
        "A60": {"new": 65000, "used": 40000},
        "A60s": {"new": 60000, "used": 38000},
        "A50": {"new": 50000, "used": 30000},
    },
    # Xiaomi/Redmi - Popular Android (Slot.ng prices)
    "Xiaomi": {
        "14 Ultra": {"new": 1800000, "used": 1200000},
        "14 Pro": {"new": 1200000, "used": 800000},
        "14": {"new": 900000, "used": 600000},
        "13 Ultra": {"new": 1200000, "used": 750000},
        "13 Pro": {"new": 900000, "used": 550000},
        "13": {"new": 650000, "used": 400000},
        "Redmi Note 13 Pro+": {"new": 380000, "used": 250000},
        "Redmi Note 13 Pro": {"new": 300000, "used": 190000},
        "Redmi Note 13": {"new": 220000, "used": 140000},
        "Redmi Note 12 Pro+": {"new": 320000, "used": 200000},
        "Redmi Note 12 Pro": {"new": 260000, "used": 160000},
        "Redmi Note 12": {"new": 180000, "used": 110000},
        "Redmi 13C": {"new": 130000, "used": 80000},
        "Redmi 12": {"new": 150000, "used": 95000},
        "Redmi A3": {"new": 85000, "used": 55000},
        "POCO X6 Pro": {"new": 450000, "used": 300000},
        "POCO X6": {"new": 350000, "used": 230000},
        "POCO X5 Pro": {"new": 320000, "used": 200000},
        "POCO M6 Pro": {"new": 200000, "used": 130000},
        "POCO C65": {"new": 120000, "used": 75000},
    },
    # Google Pixel
    "Google": {
        "Pixel 8 Pro": {"new": 1100000, "used": 700000},
        "Pixel 8": {"new": 800000, "used": 500000},
        "Pixel 8a": {"new": 600000, "used": 380000},
        "Pixel 7 Pro": {"new": 750000, "used": 450000},
        "Pixel 7": {"new": 550000, "used": 330000},
        "Pixel 7a": {"new": 450000, "used": 280000},
        "Pixel 6 Pro": {"new": 550000, "used": 320000},
        "Pixel 6": {"new": 420000, "used": 250000},
        "Pixel 6a": {"new": 350000, "used": 200000},
    },
    # OnePlus
    "OnePlus": {
        "12": {"new": 1200000, "used": 800000},
        "12R": {"new": 800000, "used": 520000},
        "11": {"new": 900000, "used": 550000},
        "11R": {"new": 650000, "used": 400000},
        "Nord 3": {"new": 450000, "used": 280000},
        "Nord CE 3": {"new": 350000, "used": 220000},
        "Nord N30": {"new": 280000, "used": 170000},
    },
    # Oppo
    "Oppo": {
        "Find X7 Ultra": {"new": 1500000, "used": 950000},
        "Find X6 Pro": {"new": 1100000, "used": 700000},
        "Reno 11 Pro": {"new": 650000, "used": 420000},
        "Reno 11": {"new": 480000, "used": 300000},
        "Reno 10 Pro+": {"new": 550000, "used": 350000},
        "Reno 10 Pro": {"new": 450000, "used": 280000},
        "Reno 10": {"new": 350000, "used": 220000},
        "A98": {"new": 320000, "used": 200000},
        "A78": {"new": 250000, "used": 160000},
        "A58": {"new": 180000, "used": 110000},
        "A18": {"new": 130000, "used": 80000},
    },
    # Vivo
    "Vivo": {
        "X100 Pro": {"new": 1300000, "used": 850000},
        "X100": {"new": 950000, "used": 600000},
        "V30 Pro": {"new": 650000, "used": 420000},
        "V30": {"new": 500000, "used": 320000},
        "V29": {"new": 450000, "used": 280000},
        "Y100": {"new": 280000, "used": 180000},
        "Y36": {"new": 180000, "used": 110000},
        "Y27": {"new": 150000, "used": 95000},
    },
    # Realme
    "Realme": {
        "GT 5 Pro": {"new": 800000, "used": 520000},
        "GT Neo 5": {"new": 550000, "used": 350000},
        "12 Pro+": {"new": 500000, "used": 320000},
        "12 Pro": {"new": 400000, "used": 260000},
        "12": {"new": 280000, "used": 180000},
        "C67": {"new": 180000, "used": 110000},
        "C55": {"new": 150000, "used": 95000},
        "C53": {"new": 130000, "used": 80000},
        "Note 50": {"new": 100000, "used": 65000},
    },
    # Nokia
    "Nokia": {
        "G42": {"new": 200000, "used": 130000},
        "G22": {"new": 150000, "used": 95000},
        "C32": {"new": 100000, "used": 65000},
        "C22": {"new": 80000, "used": 50000},
        "C12": {"new": 60000, "used": 38000},
    },
}

# Phone type detection
def is_iphone(brand: str) -> bool:
    return brand.lower() == "apple"

def get_reference_prices(brand: str, model: str) -> dict:
    """Get reference prices for a phone model"""
    brand_prices = REFERENCE_PRICES.get(brand, {})
    return brand_prices.get(model, {"new": None, "used": None})

# Web Scraper Functions
async def scrape_slot_prices(brand: str, model: str) -> List[PriceData]:
    """Scrape phone prices from slot.ng - best for Android brands"""
    prices = []
    search_query = f"{brand} {model}".replace(" ", "+")
    url = f"https://slot.ng/catalogsearch/result/?q={search_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                products = soup.find_all('div', class_='product-item-info')
                if not products:
                    products = soup.find_all('li', class_='product-item')
                if not products:
                    products = soup.find_all('div', class_='product')
                
                for product in products[:5]:
                    try:
                        title_elem = product.find('a', class_='product-item-link')
                        if not title_elem:
                            title_elem = product.find('h2') or product.find('h3') or product.find('a')
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        price_elem = product.find('span', class_='price')
                        if not price_elem:
                            price_elem = product.find('div', class_='price')
                        
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group().replace(',', ''))
                                link_elem = product.find('a', href=True)
                                product_url = link_elem['href'] if link_elem else None
                                
                                if title and (brand.lower() in title.lower() or model.lower() in title.lower()):
                                    prices.append(PriceData(
                                        source="retail",
                                        price=price,
                                        currency="NGN",
                                        url=product_url,
                                        title=title
                                    ))
                    except Exception as e:
                        logging.warning(f"Error parsing product: {e}")
                        continue
    except Exception as e:
        logging.error(f"Error scraping: {e}")
    
    return prices

async def scrape_jiji_prices(brand: str, model: str) -> List[PriceData]:
    """Scrape used phone prices from jiji.ng"""
    prices = []
    search_query = f"{brand}+{model}".lower()
    url = f"https://jiji.ng/mobile-phones?query={search_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            response = await http_client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                listings = soup.find_all('div', {'data-cy': 'adcard'})
                if not listings:
                    listings = soup.find_all('div', class_='masonry-item')
                if not listings:
                    listings = soup.find_all('article')
                
                for listing in listings[:10]:
                    try:
                        title_elem = listing.find('div', {'data-cy': 'adcard-title'})
                        if not title_elem:
                            title_elem = listing.find('h2') or listing.find('h3')
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        price_elem = listing.find('div', {'data-cy': 'adcard-price'})
                        if not price_elem:
                            price_elem = listing.find('span', class_='price') or listing.find('b')
                        
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group().replace(',', ''))
                                link_elem = listing.find('a', href=True)
                                listing_url = f"https://jiji.ng{link_elem['href']}" if link_elem and not link_elem['href'].startswith('http') else (link_elem['href'] if link_elem else None)
                                
                                if title and price > 10000:
                                    prices.append(PriceData(
                                        source="marketplace",
                                        price=price,
                                        currency="NGN",
                                        url=listing_url,
                                        title=title
                                    ))
                    except Exception as e:
                        logging.warning(f"Error parsing listing: {e}")
                        continue
    except Exception as e:
        logging.error(f"Error scraping: {e}")
    
    return prices

async def estimate_price_with_ai(
    brand: str,
    model: str,
    condition: PhoneConditionExtended,
    new_price: Optional[float],
    used_price: Optional[float]
) -> dict:
    """Use OpenAI to estimate phone price based on detailed condition"""
    
    if not EMERGENT_LLM_KEY:
        return calculate_fallback_estimate(brand, new_price, used_price, condition)
    
    try:
        from emergentintegrations.llm.openai import LlmChat
        
        new_price_str = f"₦{new_price:,.0f}" if new_price else "Unknown"
        used_price_str = f"₦{used_price:,.0f}" if used_price else "Unknown"
        
        # Build condition summary based on phone type
        condition_details = f"""
BASIC CONDITION:
- Screen: {condition.screen_condition}
- Body/Frame: {condition.body_condition}
- Battery Health: {condition.battery_health}
- Speakers: {condition.speakers_working}
- Cameras: {condition.cameras_working}
- Buttons: {condition.buttons_working}
- Network Lock: {condition.network_status}
- Original Parts: {condition.original_parts}"""

        if is_iphone(brand):
            condition_details += f"""

iPHONE SPECIFIC:
- Face ID: {condition.face_id_working or 'N/A'}
- Touch ID: {condition.touch_id_working or 'N/A'}
- iCloud Status: {condition.icloud_status or 'N/A'}
- Back Glass: {condition.back_glass_condition or 'N/A'}
- True Tone: {condition.true_tone_working or 'N/A'}"""
        else:
            condition_details += f"""

ANDROID SPECIFIC:
- Fingerprint: {condition.fingerprint_working or 'N/A'}
- FRP Status: {condition.frp_status or 'N/A'}
- Charging Port: {condition.charging_port or 'N/A'}"""

        prompt = f"""You are an expert phone valuation specialist in Nigeria. Estimate the fair resale value for a used phone.

PHONE: {brand} {model}
NEW RETAIL PRICE: {new_price_str}
CURRENT USED MARKET AVERAGE: {used_price_str}

{condition_details}

VALUATION RULES:
1. Used phones should ALWAYS be priced LOWER than new retail
2. iCloud locked iPhones lose 60-70% value
3. Cracked screens reduce value by 30-50%
4. Poor battery (<70%) reduces value by 20-30%
5. Non-working Face ID/Touch ID reduces iPhone value by 25-35%
6. FRP locked Androids lose 40-50% value
7. Non-original parts reduce value by 15-25%

Provide a JSON response:
{{"estimated_price": number_in_NGN, "confidence": "high/medium/low", "reasoning": "2-3 sentence explanation"}}

Respond ONLY with valid JSON, no markdown."""

        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"price_estimation_{uuid.uuid4()}",
            system_message="You are an expert phone valuation specialist in Nigeria."
        )
        response = await llm_chat.send_message(prompt)
        
        try:
            if hasattr(response, 'file_contents'):
                response_text = response.file_contents
            elif hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
                
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            result = json.loads(response_text)
            return {
                "estimated_price": float(result.get("estimated_price", 0)),
                "confidence": result.get("confidence", "medium"),
                "reasoning": result.get("reasoning", "AI estimation based on market data and condition.")
            }
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logging.error(f"Failed to parse AI response: {response}, Error: {e}")
            return calculate_fallback_estimate(brand, new_price, used_price, condition)
            
    except Exception as e:
        logging.error(f"AI estimation error: {e}")
        return calculate_fallback_estimate(brand, new_price, used_price, condition)

def calculate_fallback_estimate(
    brand: str,
    new_price: Optional[float],
    used_price: Optional[float],
    condition: PhoneConditionExtended
) -> dict:
    """Calculate estimate without AI"""
    
    # Base condition multipliers
    screen_mult = {"excellent": 1.0, "good": 0.92, "fair": 0.75, "cracked": 0.5}.get(condition.screen_condition, 0.75)
    body_mult = {"excellent": 1.0, "good": 0.95, "fair": 0.85, "damaged": 0.65}.get(condition.body_condition, 0.85)
    battery_mult = {"excellent": 1.0, "good": 0.92, "fair": 0.8, "poor": 0.65}.get(condition.battery_health, 0.85)
    
    # Functionality multipliers
    speakers_mult = {"yes": 1.0, "partial": 0.9, "no": 0.8}.get(condition.speakers_working, 0.95)
    cameras_mult = {"all_working": 1.0, "front_only": 0.85, "back_only": 0.85, "issues": 0.7}.get(condition.cameras_working, 0.9)
    buttons_mult = {"all_working": 1.0, "some_issues": 0.9, "major_issues": 0.75}.get(condition.buttons_working, 0.95)
    network_mult = {"unlocked": 1.0, "locked_to_carrier": 0.85}.get(condition.network_status, 0.9)
    parts_mult = {"yes": 1.0, "some_replaced": 0.9, "mostly_replaced": 0.75}.get(condition.original_parts, 0.9)
    
    # iPhone specific
    if is_iphone(brand):
        faceid_mult = {"yes": 1.0, "no": 0.7, "not_applicable": 1.0}.get(condition.face_id_working or "not_applicable", 1.0)
        touchid_mult = {"yes": 1.0, "no": 0.75, "not_applicable": 1.0}.get(condition.touch_id_working or "not_applicable", 1.0)
        icloud_mult = {"unlocked": 1.0, "locked": 0.35, "not_applicable": 1.0}.get(condition.icloud_status or "not_applicable", 1.0)
        backglass_mult = {"intact": 1.0, "cracked": 0.85, "not_applicable": 1.0}.get(condition.back_glass_condition or "not_applicable", 1.0)
        truetone_mult = {"yes": 1.0, "no": 0.95, "not_applicable": 1.0}.get(condition.true_tone_working or "not_applicable", 1.0)
        
        overall = (screen_mult + body_mult + battery_mult + speakers_mult + cameras_mult + 
                   buttons_mult + network_mult + parts_mult + faceid_mult + touchid_mult + 
                   icloud_mult + backglass_mult + truetone_mult) / 13
    else:
        # Android specific
        fingerprint_mult = {"yes": 1.0, "no": 0.9, "not_applicable": 1.0}.get(condition.fingerprint_working or "not_applicable", 1.0)
        frp_mult = {"unlocked": 1.0, "locked": 0.5, "not_applicable": 1.0}.get(condition.frp_status or "not_applicable", 1.0)
        charging_mult = {"excellent": 1.0, "good": 0.95, "loose": 0.85, "damaged": 0.7}.get(condition.charging_port or "excellent", 1.0)
        
        overall = (screen_mult + body_mult + battery_mult + speakers_mult + cameras_mult + 
                   buttons_mult + network_mult + parts_mult + fingerprint_mult + frp_mult + 
                   charging_mult) / 11
    
    # Calculate base price - used price should always be lower
    if used_price:
        base_price = used_price
    elif new_price:
        base_price = new_price * 0.60  # Used typically 60% of new
    else:
        base_price = 0
    
    estimated_price = base_price * overall
    
    # Determine confidence
    if new_price and used_price:
        confidence = "high"
    elif new_price or used_price:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "estimated_price": round(estimated_price, -2),
        "confidence": confidence,
        "reasoning": f"Estimated based on overall condition score ({overall:.0%}). Price adjusted for device condition and market rates."
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stashorra API - Phone Price Estimator"}

@api_router.get("/popular-phones")
async def get_popular_phones():
    """Get list of popular phone brands and models"""
    brands = []
    for brand_name, models in REFERENCE_PRICES.items():
        brands.append({
            "name": brand_name,
            "models": list(models.keys()),
            "type": "iphone" if brand_name == "Apple" else "android"
        })
    return {"brands": brands}

@api_router.get("/condition-questions/{brand}")
async def get_condition_questions(brand: str):
    """Get condition assessment questions based on phone type"""
    
    common_questions = [
        {
            "id": "screen_condition",
            "label": "Screen Condition",
            "description": "Check for cracks, scratches, dead pixels, or burn-in",
            "options": [
                {"value": "excellent", "label": "Excellent", "desc": "No scratches, perfect display"},
                {"value": "good", "label": "Good", "desc": "Minor scratches, not visible when screen is on"},
                {"value": "fair", "label": "Fair", "desc": "Visible scratches or minor issues"},
                {"value": "cracked", "label": "Cracked", "desc": "Cracked or shattered screen"}
            ]
        },
        {
            "id": "body_condition",
            "label": "Body/Frame Condition",
            "description": "Inspect all sides for dents, chips, or damage",
            "options": [
                {"value": "excellent", "label": "Excellent", "desc": "Like new, no visible wear"},
                {"value": "good", "label": "Good", "desc": "Minor scuffs or scratches"},
                {"value": "fair", "label": "Fair", "desc": "Noticeable dents or scratches"},
                {"value": "damaged", "label": "Damaged", "desc": "Significant damage or bent frame"}
            ]
        },
        {
            "id": "battery_health",
            "label": "Battery Health",
            "description": "Check battery health in settings",
            "options": [
                {"value": "excellent", "label": "Excellent (90-100%)", "desc": "Holds charge all day"},
                {"value": "good", "label": "Good (80-89%)", "desc": "Good battery life"},
                {"value": "fair", "label": "Fair (70-79%)", "desc": "Needs charging frequently"},
                {"value": "poor", "label": "Poor (<70%)", "desc": "Very poor battery life"}
            ]
        },
        {
            "id": "speakers_working",
            "label": "Speakers & Earpiece",
            "description": "Test audio playback and call quality",
            "options": [
                {"value": "yes", "label": "All Working", "desc": "Clear sound from all speakers"},
                {"value": "partial", "label": "Partial Issues", "desc": "Some speakers crackling or quiet"},
                {"value": "no", "label": "Not Working", "desc": "Major audio issues"}
            ]
        },
        {
            "id": "cameras_working",
            "label": "Cameras",
            "description": "Test front and back cameras",
            "options": [
                {"value": "all_working", "label": "All Working", "desc": "All cameras focus and work perfectly"},
                {"value": "front_only", "label": "Front Only", "desc": "Back camera has issues"},
                {"value": "back_only", "label": "Back Only", "desc": "Front camera has issues"},
                {"value": "issues", "label": "Major Issues", "desc": "Camera problems on both"}
            ]
        },
        {
            "id": "buttons_working",
            "label": "Physical Buttons",
            "description": "Test power, volume, and other buttons",
            "options": [
                {"value": "all_working", "label": "All Working", "desc": "All buttons click and respond"},
                {"value": "some_issues", "label": "Some Issues", "desc": "Some buttons sticky or unresponsive"},
                {"value": "major_issues", "label": "Major Issues", "desc": "Multiple buttons not working"}
            ]
        },
        {
            "id": "network_status",
            "label": "Network Lock Status",
            "description": "Is the phone unlocked to all networks?",
            "options": [
                {"value": "unlocked", "label": "Unlocked", "desc": "Works with any carrier SIM"},
                {"value": "locked_to_carrier", "label": "Carrier Locked", "desc": "Only works with specific carrier"}
            ]
        },
        {
            "id": "original_parts",
            "label": "Original Parts",
            "description": "Are all parts original?",
            "options": [
                {"value": "yes", "label": "All Original", "desc": "No parts replaced"},
                {"value": "some_replaced", "label": "Some Replaced", "desc": "Screen or battery replaced"},
                {"value": "mostly_replaced", "label": "Mostly Replaced", "desc": "Multiple parts not original"}
            ]
        }
    ]
    
    iphone_questions = [
        {
            "id": "face_id_working",
            "label": "Face ID",
            "description": "Test Face ID unlock and Apple Pay",
            "options": [
                {"value": "yes", "label": "Working", "desc": "Face ID works perfectly"},
                {"value": "no", "label": "Not Working", "desc": "Face ID disabled or broken"},
                {"value": "not_applicable", "label": "N/A", "desc": "Device doesn't have Face ID"}
            ]
        },
        {
            "id": "touch_id_working",
            "label": "Touch ID",
            "description": "Test fingerprint sensor",
            "options": [
                {"value": "yes", "label": "Working", "desc": "Touch ID works perfectly"},
                {"value": "no", "label": "Not Working", "desc": "Touch ID not responding"},
                {"value": "not_applicable", "label": "N/A", "desc": "Device doesn't have Touch ID"}
            ]
        },
        {
            "id": "icloud_status",
            "label": "iCloud Lock Status",
            "description": "CRITICAL: Is the device signed out of iCloud?",
            "options": [
                {"value": "unlocked", "label": "Unlocked/Signed Out", "desc": "No iCloud account linked"},
                {"value": "locked", "label": "iCloud Locked", "desc": "Previous owner's account still linked"}
            ]
        },
        {
            "id": "back_glass_condition",
            "label": "Back Glass",
            "description": "Check the back glass panel",
            "options": [
                {"value": "intact", "label": "Intact", "desc": "No cracks on back glass"},
                {"value": "cracked", "label": "Cracked", "desc": "Back glass is cracked"},
                {"value": "not_applicable", "label": "N/A", "desc": "Device has metal back"}
            ]
        },
        {
            "id": "true_tone_working",
            "label": "True Tone Display",
            "description": "Check if True Tone is available in display settings",
            "options": [
                {"value": "yes", "label": "Working", "desc": "True Tone available and working"},
                {"value": "no", "label": "Not Working", "desc": "True Tone disabled (screen replaced)"},
                {"value": "not_applicable", "label": "N/A", "desc": "Device doesn't support True Tone"}
            ]
        }
    ]
    
    android_questions = [
        {
            "id": "fingerprint_working",
            "label": "Fingerprint Sensor",
            "description": "Test the fingerprint scanner",
            "options": [
                {"value": "yes", "label": "Working", "desc": "Fingerprint works perfectly"},
                {"value": "no", "label": "Not Working", "desc": "Fingerprint not responding"},
                {"value": "not_applicable", "label": "N/A", "desc": "Device has no fingerprint sensor"}
            ]
        },
        {
            "id": "frp_status",
            "label": "FRP (Google Lock) Status",
            "description": "CRITICAL: Is Factory Reset Protection disabled?",
            "options": [
                {"value": "unlocked", "label": "Unlocked", "desc": "No Google account linked after reset"},
                {"value": "locked", "label": "FRP Locked", "desc": "Previous Google account still required"}
            ]
        },
        {
            "id": "charging_port",
            "label": "Charging Port Condition",
            "description": "Test charging cable connection",
            "options": [
                {"value": "excellent", "label": "Excellent", "desc": "Charges perfectly, tight fit"},
                {"value": "good", "label": "Good", "desc": "Works well, minor wear"},
                {"value": "loose", "label": "Loose", "desc": "Cable doesn't hold firmly"},
                {"value": "damaged", "label": "Damaged", "desc": "Charging issues or port damage"}
            ]
        }
    ]
    
    if is_iphone(brand):
        return {"questions": common_questions + iphone_questions}
    else:
        return {"questions": common_questions + android_questions}

@api_router.post("/search-phone", response_model=ScrapedPrices)
async def search_phone_prices(request: PhoneSearchRequest):
    """Search for phone prices"""
    
    import asyncio
    
    # For Android brands, prefer Slot.ng for new prices
    # For Apple, use reference prices (Jiji for used)
    if is_iphone(request.brand):
        # iPhone - skip slot.ng, use reference for new, jiji for used
        slot_prices = []
        jiji_prices = await scrape_jiji_prices(request.brand, request.model)
    else:
        # Android - try slot.ng for new prices
        slot_task = scrape_slot_prices(request.brand, request.model)
        jiji_task = scrape_jiji_prices(request.brand, request.model)
        slot_prices, jiji_prices = await asyncio.gather(slot_task, jiji_task)
    
    # Get reference prices as fallback
    ref_prices = get_reference_prices(request.brand, request.model)
    
    new_prices = slot_prices if slot_prices else []
    used_prices = jiji_prices if jiji_prices else []
    
    # Add reference prices if scraping returned nothing
    if not new_prices and ref_prices["new"]:
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
    
    return ScrapedPrices(
        new_prices=new_prices,
        used_prices=used_prices
    )

@api_router.post("/estimate-price", response_model=PriceEstimate)
async def estimate_price(request: PriceEstimateRequest):
    """Estimate the price of a used phone based on detailed condition"""
    
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
    
    # Save to MongoDB
    doc = estimate.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.estimates.insert_one(doc)
    
    return estimate

@api_router.get("/estimates", response_model=List[PriceEstimate])
async def get_estimates(limit: int = 10):
    """Get recent price estimates"""
    estimates = await db.estimates.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    for est in estimates:
        if isinstance(est.get('timestamp'), str):
            est['timestamp'] = datetime.fromisoformat(est['timestamp'])
    
    return estimates

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
