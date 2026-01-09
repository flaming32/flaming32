from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
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

class PhoneCondition(BaseModel):
    screen_condition: str  # excellent, good, fair, poor
    battery_health: str    # excellent, good, fair, poor
    physical_damage: str   # none, minor, moderate, severe

class PriceEstimateRequest(BaseModel):
    brand: str
    model: str
    condition: PhoneCondition
    slot_price: Optional[float] = None
    jiji_prices: Optional[List[float]] = None

class PriceData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str
    price: Optional[float] = None
    currency: str = "NGN"
    url: Optional[str] = None
    title: Optional[str] = None

class ScrapedPrices(BaseModel):
    model_config = ConfigDict(extra="ignore")
    slot_prices: List[PriceData]
    jiji_prices: List[PriceData]

class PriceEstimate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: str
    model: str
    condition: PhoneCondition
    new_price_avg: Optional[float] = None
    used_price_avg: Optional[float] = None
    estimated_price: float
    confidence: str
    reasoning: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Web Scraper Functions
async def scrape_slot_prices(brand: str, model: str) -> List[PriceData]:
    """Scrape phone prices from slot.ng"""
    prices = []
    search_query = f"{brand} {model}".replace(" ", "+")
    url = f"https://slot.ng/catalogsearch/result/?q={search_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find product items
                products = soup.find_all('div', class_='product-item-info')
                if not products:
                    products = soup.find_all('li', class_='product-item')
                if not products:
                    products = soup.find_all('div', class_='product')
                
                for product in products[:5]:
                    try:
                        # Find title
                        title_elem = product.find('a', class_='product-item-link')
                        if not title_elem:
                            title_elem = product.find('h2') or product.find('h3') or product.find('a')
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        # Find price
                        price_elem = product.find('span', class_='price')
                        if not price_elem:
                            price_elem = product.find('div', class_='price')
                        
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            # Extract numeric value
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group().replace(',', ''))
                                
                                # Get product URL
                                link_elem = product.find('a', href=True)
                                product_url = link_elem['href'] if link_elem else None
                                
                                # Verify this is a relevant phone
                                if title and (brand.lower() in title.lower() or model.lower() in title.lower()):
                                    prices.append(PriceData(
                                        source="slot.ng",
                                        price=price,
                                        currency="NGN",
                                        url=product_url,
                                        title=title
                                    ))
                    except Exception as e:
                        logging.warning(f"Error parsing slot product: {e}")
                        continue
    except Exception as e:
        logging.error(f"Error scraping slot.ng: {e}")
    
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
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find listings
                listings = soup.find_all('div', {'data-cy': 'adcard'})
                if not listings:
                    listings = soup.find_all('div', class_='masonry-item')
                if not listings:
                    listings = soup.find_all('article')
                
                for listing in listings[:10]:
                    try:
                        # Find title
                        title_elem = listing.find('div', {'data-cy': 'adcard-title'})
                        if not title_elem:
                            title_elem = listing.find('h2') or listing.find('h3')
                        title = title_elem.get_text(strip=True) if title_elem else None
                        
                        # Find price
                        price_elem = listing.find('div', {'data-cy': 'adcard-price'})
                        if not price_elem:
                            price_elem = listing.find('span', class_='price') or listing.find('b')
                        
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                            if price_match:
                                price = float(price_match.group().replace(',', ''))
                                
                                # Get listing URL
                                link_elem = listing.find('a', href=True)
                                listing_url = f"https://jiji.ng{link_elem['href']}" if link_elem and not link_elem['href'].startswith('http') else (link_elem['href'] if link_elem else None)
                                
                                # Verify relevance
                                if title and price > 10000:  # Filter out unrealistic prices
                                    prices.append(PriceData(
                                        source="jiji.ng",
                                        price=price,
                                        currency="NGN",
                                        url=listing_url,
                                        title=title
                                    ))
                    except Exception as e:
                        logging.warning(f"Error parsing jiji listing: {e}")
                        continue
    except Exception as e:
        logging.error(f"Error scraping jiji.ng: {e}")
    
    return prices

async def estimate_price_with_ai(
    brand: str,
    model: str,
    condition: PhoneCondition,
    new_price: Optional[float],
    used_prices: Optional[List[float]]
) -> dict:
    """Use OpenAI to estimate phone price based on condition"""
    
    if not EMERGENT_LLM_KEY:
        # Fallback estimation without AI
        return calculate_fallback_estimate(new_price, used_prices, condition)
    
    try:
        from emergentintegrations.llm.openai import LlmChat
        
        # Calculate averages for context
        new_price_str = f"₦{new_price:,.0f}" if new_price else "Unknown"
        used_avg = sum(used_prices) / len(used_prices) if used_prices else None
        used_price_str = f"₦{used_avg:,.0f}" if used_avg else "Unknown"
        
        prompt = f"""You are an expert phone valuation specialist in Nigeria. Estimate the fair market value for a used phone based on the following:

PHONE: {brand} {model}
NEW PRICE (Slot.ng): {new_price_str}
USED MARKET PRICE (Jiji.ng average): {used_price_str}

CONDITION ASSESSMENT:
- Screen Condition: {condition.screen_condition}
- Battery Health: {condition.battery_health}
- Physical Damage: {condition.physical_damage}

Provide a JSON response with:
1. estimated_price: Your fair price estimate in NGN (number only)
2. confidence: "high", "medium", or "low"
3. reasoning: Brief 2-3 sentence explanation

Consider:
- Excellent condition: 70-85% of new price
- Good condition: 55-70% of new price
- Fair condition: 40-55% of new price
- Poor condition: 25-40% of new price

Respond ONLY with valid JSON, no markdown:
{{"estimated_price": number, "confidence": "string", "reasoning": "string"}}"""

        llm_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id="price_estimation",
            system_message="You are an expert phone valuation specialist in Nigeria."
        )
        response = await llm_chat.send_message(prompt)
        
        # Parse the AI response
        try:
            # Handle different response types
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
            return calculate_fallback_estimate(new_price, used_prices, condition)
            
    except Exception as e:
        logging.error(f"AI estimation error: {e}")
        return calculate_fallback_estimate(new_price, used_prices, condition)

def calculate_fallback_estimate(
    new_price: Optional[float],
    used_prices: Optional[List[float]],
    condition: PhoneCondition
) -> dict:
    """Calculate estimate without AI"""
    
    # Condition multipliers
    condition_scores = {
        "screen_condition": {"excellent": 1.0, "good": 0.85, "fair": 0.65, "poor": 0.4},
        "battery_health": {"excellent": 1.0, "good": 0.9, "fair": 0.75, "poor": 0.5},
        "physical_damage": {"none": 1.0, "minor": 0.9, "moderate": 0.7, "severe": 0.4}
    }
    
    screen_mult = condition_scores["screen_condition"].get(condition.screen_condition, 0.7)
    battery_mult = condition_scores["battery_health"].get(condition.battery_health, 0.75)
    damage_mult = condition_scores["physical_damage"].get(condition.physical_damage, 0.8)
    
    overall_condition = (screen_mult + battery_mult + damage_mult) / 3
    
    # Base price calculation
    base_price = None
    if new_price:
        base_price = new_price * 0.65  # Used phones typically 65% of new
    elif used_prices:
        base_price = sum(used_prices) / len(used_prices)
    
    if base_price:
        estimated_price = base_price * overall_condition
        confidence = "medium" if new_price or used_prices else "low"
    else:
        estimated_price = 0
        confidence = "low"
    
    return {
        "estimated_price": round(estimated_price, -2),  # Round to nearest 100
        "confidence": confidence,
        "reasoning": f"Estimated based on condition score ({overall_condition:.0%}). " + 
                    ("Using new retail price as baseline." if new_price else "Using market used prices as baseline." if used_prices else "No market data available.")
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stashorra API - Phone Price Estimator"}

@api_router.post("/search-phone", response_model=ScrapedPrices)
async def search_phone_prices(request: PhoneSearchRequest):
    """Search for phone prices on slot.ng and jiji.ng"""
    
    # Run both scrapers concurrently
    import asyncio
    slot_task = scrape_slot_prices(request.brand, request.model)
    jiji_task = scrape_jiji_prices(request.brand, request.model)
    
    slot_prices, jiji_prices = await asyncio.gather(slot_task, jiji_task)
    
    # If scraping returns no results, use reference prices
    ref_prices = get_reference_prices(request.brand, request.model)
    
    if not slot_prices and ref_prices["new"]:
        slot_prices = [PriceData(
            source="slot.ng (reference)",
            price=ref_prices["new"],
            currency="NGN",
            url=f"https://slot.ng/catalogsearch/result/?q={request.brand}+{request.model}",
            title=f"{request.brand} {request.model} (New)"
        )]
    
    if not jiji_prices and ref_prices["used"]:
        jiji_prices = [PriceData(
            source="jiji.ng (reference)",
            price=ref_prices["used"],
            currency="NGN",
            url=f"https://jiji.ng/mobile-phones?query={request.brand}+{request.model}",
            title=f"{request.brand} {request.model} (Used)"
        )]
    
    return ScrapedPrices(
        slot_prices=slot_prices,
        jiji_prices=jiji_prices
    )

@api_router.post("/estimate-price", response_model=PriceEstimate)
async def estimate_price(request: PriceEstimateRequest):
    """Estimate the price of a used phone based on condition"""
    
    # Get used prices as list of floats
    used_price_list = request.jiji_prices if request.jiji_prices else []
    
    # Get AI estimation
    ai_result = await estimate_price_with_ai(
        brand=request.brand,
        model=request.model,
        condition=request.condition,
        new_price=request.slot_price,
        used_prices=used_price_list
    )
    
    # Calculate averages
    new_price_avg = request.slot_price
    used_price_avg = sum(used_price_list) / len(used_price_list) if used_price_list else None
    
    # Create estimate object
    estimate = PriceEstimate(
        brand=request.brand,
        model=request.model,
        condition=request.condition,
        new_price_avg=new_price_avg,
        used_price_avg=used_price_avg,
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

# Reference prices for common phones (in NGN) - used as fallback when scraping fails
REFERENCE_PRICES = {
    "Apple": {
        "iPhone 15 Pro Max": {"new": 2200000, "used": 1700000},
        "iPhone 15 Pro": {"new": 1900000, "used": 1500000},
        "iPhone 15": {"new": 1400000, "used": 1100000},
        "iPhone 14 Pro Max": {"new": 1600000, "used": 1200000},
        "iPhone 14": {"new": 1100000, "used": 850000},
        "iPhone 13": {"new": 850000, "used": 650000},
        "iPhone 12": {"new": 650000, "used": 480000},
        "iPhone 11": {"new": 480000, "used": 350000},
    },
    "Samsung": {
        "Galaxy S24 Ultra": {"new": 2100000, "used": 1600000},
        "Galaxy S24+": {"new": 1500000, "used": 1150000},
        "Galaxy S24": {"new": 1200000, "used": 900000},
        "Galaxy S23 Ultra": {"new": 1400000, "used": 1050000},
        "Galaxy A54": {"new": 380000, "used": 280000},
        "Galaxy A34": {"new": 280000, "used": 200000},
        "Galaxy Z Fold 5": {"new": 2800000, "used": 2100000},
        "Galaxy Z Flip 5": {"new": 1300000, "used": 950000},
    },
    "Google": {
        "Pixel 8 Pro": {"new": 950000, "used": 720000},
        "Pixel 8": {"new": 650000, "used": 480000},
        "Pixel 7 Pro": {"new": 580000, "used": 420000},
        "Pixel 7": {"new": 450000, "used": 320000},
        "Pixel 6a": {"new": 320000, "used": 220000},
    },
    "Tecno": {
        "Camon 20 Pro": {"new": 280000, "used": 200000},
        "Camon 20": {"new": 180000, "used": 130000},
        "Spark 10 Pro": {"new": 150000, "used": 100000},
        "Pova 5": {"new": 160000, "used": 110000},
        "Phantom X2": {"new": 450000, "used": 320000},
    },
    "Infinix": {
        "Note 30 Pro": {"new": 220000, "used": 160000},
        "Note 30": {"new": 170000, "used": 120000},
        "Hot 30": {"new": 120000, "used": 85000},
        "Zero 30": {"new": 280000, "used": 200000},
        "Smart 8": {"new": 95000, "used": 65000},
    },
    "Xiaomi": {
        "Redmi Note 13 Pro": {"new": 280000, "used": 200000},
        "Redmi Note 12": {"new": 180000, "used": 130000},
        "POCO X5 Pro": {"new": 320000, "used": 230000},
        "POCO M5": {"new": 150000, "used": 100000},
    },
}

def get_reference_prices(brand: str, model: str) -> dict:
    """Get reference prices for a phone model"""
    brand_prices = REFERENCE_PRICES.get(brand, {})
    return brand_prices.get(model, {"new": None, "used": None})

@api_router.get("/popular-phones")
async def get_popular_phones():
    """Get list of popular phone brands and models"""
    return {
        "brands": [
            {"name": "Apple", "models": ["iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15", "iPhone 14 Pro Max", "iPhone 14", "iPhone 13", "iPhone 12", "iPhone 11"]},
            {"name": "Samsung", "models": ["Galaxy S24 Ultra", "Galaxy S24+", "Galaxy S24", "Galaxy S23 Ultra", "Galaxy A54", "Galaxy A34", "Galaxy Z Fold 5", "Galaxy Z Flip 5"]},
            {"name": "Google", "models": ["Pixel 8 Pro", "Pixel 8", "Pixel 7 Pro", "Pixel 7", "Pixel 6a"]},
            {"name": "Tecno", "models": ["Camon 20 Pro", "Camon 20", "Spark 10 Pro", "Pova 5", "Phantom X2"]},
            {"name": "Infinix", "models": ["Note 30 Pro", "Note 30", "Hot 30", "Zero 30", "Smart 8"]},
            {"name": "Xiaomi", "models": ["Redmi Note 13 Pro", "Redmi Note 12", "POCO X5 Pro", "POCO M5"]},
        ]
    }

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
