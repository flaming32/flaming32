from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import secrets
import string
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
import re
import json
import asyncio
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI setup via Emergent
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Resend Email setup
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Olaoluwa32$"

# Payment packages
PAYMENT_PACKAGES = {
    "basic": {
        "name": "Basic",
        "amount": 400,
        "uses": 2,
        "description": "2 price estimates"
    },
    "reseller": {
        "name": "Reseller Pack",
        "amount": 3000,
        "codes_count": 20,
        "uses_per_code": 1,
        "description": "20 codes to distribute (₦150 each!)"
    }
}

PAYMENT_INFO = {
    "account_number": "3002978669",
    "bank_name": "KUDA MFB",
    "account_name": "STASHORRA STORE",
    "email": "support@stashorra.store",
    "packages": PAYMENT_PACKAGES
}

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
    access_code: str

class PriceData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str
    price: Optional[float] = None
    currency: str = "NGN"

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

class AccessCodeVerify(BaseModel):
    code: str

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminGenerateCode(BaseModel):
    username: str
    password: str
    note: Optional[str] = None
    package: str = "basic"
    send_email: bool = False
    recipient_email: Optional[str] = None

class ResellerDashboardRequest(BaseModel):
    master_code: str

class EmailNotification(BaseModel):
    recipient_email: EmailStr
    access_code: str
    package_name: str
    uses: int

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
    "iPhone 8 Plus", "iPhone 8", "iPhone 7 Plus", "iPhone 7",
    "iPhone 6s Plus", "iPhone 6s", "iPhone 6 Plus", "iPhone 6"
]

# Expanded reference prices with more models
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
        "Galaxy S25 Ultra": {"new": 2400000, "used": 1200000},
        "Galaxy S25+": {"new": 1800000, "used": 900000},
        "Galaxy S25": {"new": 1400000, "used": 700000},
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
        "Galaxy Z Fold 6": {"new": 3200000, "used": 1600000},
        "Galaxy Z Fold 5": {"new": 2800000, "used": 1400000},
        "Galaxy Z Fold 4": {"new": 2000000, "used": 850000},
        "Galaxy Z Flip 6": {"new": 1500000, "used": 750000},
        "Galaxy Z Flip 5": {"new": 1300000, "used": 550000},
        "Galaxy Z Flip 4": {"new": 900000, "used": 350000},
        "Galaxy A55": {"new": 450000, "used": 200000},
        "Galaxy A54": {"new": 380000, "used": 150000},
        "Galaxy A35": {"new": 320000, "used": 140000},
        "Galaxy A34": {"new": 280000, "used": 110000},
        "Galaxy A25": {"new": 220000, "used": 95000},
        "Galaxy A24": {"new": 200000, "used": 80000},
        "Galaxy A15": {"new": 160000, "used": 65000},
        "Galaxy A14": {"new": 150000, "used": 55000},
        "Galaxy A05s": {"new": 120000, "used": 45000},
        "Galaxy A05": {"new": 100000, "used": 35000},
        "Galaxy M55": {"new": 400000, "used": 170000},
        "Galaxy M54": {"new": 350000, "used": 140000},
        "Galaxy M34": {"new": 250000, "used": 100000},
    },
    "Tecno": {
        "Phantom X2 Pro": {"new": 550000, "used": 220000},
        "Phantom X2": {"new": 450000, "used": 170000},
        "Phantom V Fold": {"new": 900000, "used": 400000},
        "Phantom V Flip": {"new": 550000, "used": 220000},
        "Camon 30 Pro": {"new": 350000, "used": 140000},
        "Camon 30 Premier": {"new": 400000, "used": 160000},
        "Camon 30": {"new": 280000, "used": 110000},
        "Camon 20 Pro": {"new": 280000, "used": 100000},
        "Camon 20 Premier": {"new": 320000, "used": 120000},
        "Camon 20": {"new": 180000, "used": 65000},
        "Camon 19 Pro": {"new": 200000, "used": 70000},
        "Camon 19": {"new": 150000, "used": 50000},
        "Spark 30 Pro": {"new": 200000, "used": 80000},
        "Spark 30": {"new": 150000, "used": 55000},
        "Spark 20 Pro+": {"new": 220000, "used": 85000},
        "Spark 20 Pro": {"new": 180000, "used": 65000},
        "Spark 20": {"new": 130000, "used": 45000},
        "Spark 20C": {"new": 100000, "used": 35000},
        "Spark 10 Pro": {"new": 150000, "used": 50000},
        "Spark 10": {"new": 100000, "used": 35000},
        "Spark Go 2024": {"new": 75000, "used": 25000},
        "Pova 6 Pro": {"new": 280000, "used": 110000},
        "Pova 6 Neo": {"new": 200000, "used": 75000},
        "Pova 6": {"new": 200000, "used": 75000},
        "Pova 5 Pro": {"new": 200000, "used": 70000},
        "Pova 5": {"new": 160000, "used": 55000},
        "Pop 8": {"new": 80000, "used": 28000},
        "Pop 7 Pro": {"new": 70000, "used": 24000},
        "Pop 7": {"new": 65000, "used": 22000},
    },
    "Infinix": {
        "GT 20 Pro": {"new": 400000, "used": 160000},
        "Zero 40": {"new": 400000, "used": 160000},
        "Zero 30": {"new": 350000, "used": 140000},
        "Zero 20": {"new": 280000, "used": 100000},
        "Note 40 Pro+": {"new": 380000, "used": 150000},
        "Note 40 Pro": {"new": 320000, "used": 125000},
        "Note 40": {"new": 250000, "used": 95000},
        "Note 30 Pro": {"new": 220000, "used": 80000},
        "Note 30 VIP": {"new": 280000, "used": 110000},
        "Note 30": {"new": 170000, "used": 60000},
        "Hot 50 Pro+": {"new": 200000, "used": 75000},
        "Hot 50 Pro": {"new": 180000, "used": 65000},
        "Hot 50": {"new": 140000, "used": 50000},
        "Hot 50i": {"new": 100000, "used": 35000},
        "Hot 40 Pro": {"new": 180000, "used": 65000},
        "Hot 40": {"new": 140000, "used": 50000},
        "Hot 40i": {"new": 110000, "used": 38000},
        "Hot 30 Play": {"new": 100000, "used": 35000},
        "Hot 30": {"new": 120000, "used": 42000},
        "Hot 30i": {"new": 90000, "used": 30000},
        "Smart 9": {"new": 100000, "used": 35000},
        "Smart 8 Plus": {"new": 110000, "used": 38000},
        "Smart 8": {"new": 95000, "used": 32000},
        "Smart 8 HD": {"new": 80000, "used": 28000},
    },
    "Itel": {
        "S25": {"new": 140000, "used": 50000},
        "S24": {"new": 130000, "used": 45000},
        "S23+": {"new": 110000, "used": 38000},
        "S23": {"new": 90000, "used": 30000},
        "P65": {"new": 110000, "used": 38000},
        "P55+": {"new": 100000, "used": 35000},
        "P55T": {"new": 95000, "used": 32000},
        "P55": {"new": 80000, "used": 28000},
        "P40+": {"new": 70000, "used": 24000},
        "P40": {"new": 55000, "used": 18000},
        "A95 5G": {"new": 130000, "used": 45000},
        "A90": {"new": 100000, "used": 35000},
        "A70": {"new": 85000, "used": 28000},
        "A60s": {"new": 60000, "used": 20000},
        "A60": {"new": 65000, "used": 22000},
        "A50": {"new": 50000, "used": 16000},
        "Vision 5": {"new": 75000, "used": 26000},
        "Vision 3": {"new": 55000, "used": 18000},
    },
    "Xiaomi": {
        "14 Ultra": {"new": 1800000, "used": 800000},
        "14 Pro": {"new": 1200000, "used": 500000},
        "14": {"new": 900000, "used": 380000},
        "13 Ultra": {"new": 1200000, "used": 450000},
        "13 Pro": {"new": 900000, "used": 340000},
        "13T Pro": {"new": 750000, "used": 300000},
        "13T": {"new": 550000, "used": 220000},
        "13": {"new": 650000, "used": 250000},
        "12 Pro": {"new": 700000, "used": 260000},
        "12": {"new": 500000, "used": 180000},
    },
    "Redmi": {
        "Note 14 Pro+": {"new": 420000, "used": 170000},
        "Note 14 Pro": {"new": 350000, "used": 140000},
        "Note 14": {"new": 250000, "used": 95000},
        "Note 13 Pro+": {"new": 380000, "used": 150000},
        "Note 13 Pro": {"new": 300000, "used": 115000},
        "Note 13": {"new": 220000, "used": 80000},
        "Note 12 Pro+": {"new": 320000, "used": 120000},
        "Note 12 Pro": {"new": 260000, "used": 95000},
        "Note 12": {"new": 180000, "used": 65000},
        "14C": {"new": 150000, "used": 55000},
        "13C": {"new": 130000, "used": 45000},
        "12": {"new": 150000, "used": 52000},
        "A3": {"new": 85000, "used": 28000},
        "A2": {"new": 70000, "used": 24000},
    },
    "Poco": {
        "F6 Pro": {"new": 650000, "used": 280000},
        "F6": {"new": 500000, "used": 200000},
        "X6 Pro": {"new": 450000, "used": 180000},
        "X6": {"new": 350000, "used": 140000},
        "X5 Pro": {"new": 320000, "used": 120000},
        "X5": {"new": 250000, "used": 95000},
        "M6 Pro": {"new": 200000, "used": 75000},
        "M6": {"new": 150000, "used": 55000},
        "C75": {"new": 130000, "used": 48000},
        "C65": {"new": 120000, "used": 42000},
        "C55": {"new": 100000, "used": 35000},
    },
    "Google": {
        "Pixel 9 Pro XL": {"new": 1500000, "used": 750000},
        "Pixel 9 Pro": {"new": 1300000, "used": 650000},
        "Pixel 9": {"new": 1000000, "used": 480000},
        "Pixel 9a": {"new": 700000, "used": 320000},
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
        "13": {"new": 1400000, "used": 700000},
        "13R": {"new": 900000, "used": 400000},
        "12": {"new": 1200000, "used": 520000},
        "12R": {"new": 800000, "used": 320000},
        "11": {"new": 900000, "used": 340000},
        "11R": {"new": 650000, "used": 250000},
        "Nord 4": {"new": 550000, "used": 220000},
        "Nord 3": {"new": 450000, "used": 170000},
        "Nord CE 4": {"new": 400000, "used": 160000},
        "Nord CE 3": {"new": 350000, "used": 130000},
        "Nord N30": {"new": 280000, "used": 100000},
    },
    "Oppo": {
        "Find X8 Pro": {"new": 1600000, "used": 700000},
        "Find X8": {"new": 1200000, "used": 520000},
        "Find X7 Ultra": {"new": 1500000, "used": 650000},
        "Find X7": {"new": 1100000, "used": 450000},
        "Reno 12 Pro": {"new": 700000, "used": 300000},
        "Reno 12": {"new": 550000, "used": 220000},
        "Reno 11 Pro": {"new": 650000, "used": 260000},
        "Reno 11 F": {"new": 450000, "used": 180000},
        "Reno 11": {"new": 480000, "used": 180000},
        "Reno 10 Pro+": {"new": 550000, "used": 210000},
        "A98": {"new": 320000, "used": 120000},
        "A79": {"new": 280000, "used": 105000},
        "A78": {"new": 250000, "used": 90000},
        "A58": {"new": 180000, "used": 65000},
        "A38": {"new": 150000, "used": 55000},
        "A18": {"new": 130000, "used": 45000},
    },
    "Vivo": {
        "X200 Pro": {"new": 1500000, "used": 700000},
        "X200": {"new": 1100000, "used": 480000},
        "X100 Pro": {"new": 1300000, "used": 550000},
        "X100": {"new": 950000, "used": 380000},
        "V40 Pro": {"new": 750000, "used": 320000},
        "V40": {"new": 600000, "used": 250000},
        "V30 Pro": {"new": 650000, "used": 260000},
        "V30": {"new": 500000, "used": 190000},
        "V29": {"new": 450000, "used": 170000},
        "Y200 Pro": {"new": 350000, "used": 140000},
        "Y200": {"new": 280000, "used": 105000},
        "Y100": {"new": 280000, "used": 105000},
        "Y36": {"new": 180000, "used": 65000},
        "Y27": {"new": 150000, "used": 52000},
        "Y18": {"new": 120000, "used": 42000},
    },
    "Realme": {
        "GT 6": {"new": 750000, "used": 320000},
        "GT 5 Pro": {"new": 800000, "used": 320000},
        "GT Neo 6": {"new": 600000, "used": 240000},
        "GT Neo 5": {"new": 550000, "used": 210000},
        "13 Pro+": {"new": 550000, "used": 220000},
        "13 Pro": {"new": 450000, "used": 180000},
        "13": {"new": 350000, "used": 140000},
        "12 Pro+": {"new": 500000, "used": 190000},
        "12 Pro": {"new": 400000, "used": 150000},
        "12": {"new": 280000, "used": 105000},
        "C67": {"new": 180000, "used": 65000},
        "C65": {"new": 150000, "used": 55000},
        "C55": {"new": 150000, "used": 52000},
        "C53": {"new": 130000, "used": 45000},
        "Note 60": {"new": 120000, "used": 42000},
        "Note 50": {"new": 100000, "used": 35000},
    },
    "Huawei": {
        "Pura 70 Ultra": {"new": 2000000, "used": 900000},
        "Pura 70 Pro": {"new": 1600000, "used": 700000},
        "Pura 70": {"new": 1200000, "used": 500000},
        "Mate 60 Pro+": {"new": 1800000, "used": 800000},
        "Mate 60 Pro": {"new": 1500000, "used": 650000},
        "Mate 60": {"new": 1200000, "used": 500000},
        "P60 Pro": {"new": 1100000, "used": 450000},
        "P60": {"new": 900000, "used": 360000},
        "Nova 12 Ultra": {"new": 650000, "used": 260000},
        "Nova 12 Pro": {"new": 550000, "used": 210000},
        "Nova 12": {"new": 400000, "used": 150000},
        "Nova 11 Pro": {"new": 450000, "used": 170000},
        "Nova 11": {"new": 350000, "used": 130000},
        "Nova Y91": {"new": 180000, "used": 65000},
        "Nova Y72": {"new": 150000, "used": 52000},
    },
    "Honor": {
        "Magic 7 Pro": {"new": 1400000, "used": 600000},
        "Magic 7": {"new": 1000000, "used": 420000},
        "Magic 6 Pro": {"new": 1200000, "used": 500000},
        "Magic 6": {"new": 900000, "used": 360000},
        "200 Pro": {"new": 850000, "used": 350000},
        "200": {"new": 650000, "used": 260000},
        "90 Pro": {"new": 650000, "used": 250000},
        "90": {"new": 480000, "used": 180000},
        "X9c": {"new": 400000, "used": 160000},
        "X9b": {"new": 350000, "used": 130000},
        "X8b": {"new": 280000, "used": 100000},
        "X7b": {"new": 200000, "used": 72000},
    },
    "Nokia": {
        "G60": {"new": 280000, "used": 100000},
        "G42": {"new": 200000, "used": 70000},
        "G22": {"new": 150000, "used": 52000},
        "G21": {"new": 130000, "used": 45000},
        "C32": {"new": 100000, "used": 35000},
        "C22": {"new": 80000, "used": 28000},
        "C12 Pro": {"new": 70000, "used": 24000},
        "C12": {"new": 60000, "used": 20000},
    },
    "Motorola": {
        "Edge 50 Ultra": {"new": 900000, "used": 380000},
        "Edge 50 Pro": {"new": 700000, "used": 280000},
        "Edge 50": {"new": 550000, "used": 220000},
        "Edge 40 Pro": {"new": 750000, "used": 300000},
        "Edge 40": {"new": 550000, "used": 210000},
        "Razr 50 Ultra": {"new": 1400000, "used": 600000},
        "Razr 50": {"new": 1000000, "used": 420000},
        "G85": {"new": 380000, "used": 150000},
        "G84": {"new": 350000, "used": 130000},
        "G54": {"new": 250000, "used": 90000},
        "G34": {"new": 180000, "used": 65000},
        "G24": {"new": 140000, "used": 50000},
        "E14": {"new": 110000, "used": 38000},
        "E13": {"new": 100000, "used": 35000},
    },
    "Sony": {
        "Xperia 1 VI": {"new": 1600000, "used": 700000},
        "Xperia 1 V": {"new": 1400000, "used": 600000},
        "Xperia 5 V": {"new": 1000000, "used": 400000},
        "Xperia 10 VI": {"new": 600000, "used": 240000},
        "Xperia 10 V": {"new": 550000, "used": 210000},
    },
    "Asus": {
        "ROG Phone 9 Pro": {"new": 1800000, "used": 800000},
        "ROG Phone 9": {"new": 1400000, "used": 600000},
        "ROG Phone 8 Pro": {"new": 1500000, "used": 650000},
        "ROG Phone 8": {"new": 1200000, "used": 500000},
        "Zenfone 11 Ultra": {"new": 1100000, "used": 450000},
        "Zenfone 10": {"new": 900000, "used": 360000},
    },
    "iQOO": {
        "13": {"new": 900000, "used": 380000},
        "12 Pro": {"new": 800000, "used": 320000},
        "12": {"new": 650000, "used": 260000},
        "Neo 9 Pro": {"new": 550000, "used": 220000},
        "Neo 9": {"new": 450000, "used": 170000},
        "Z9": {"new": 350000, "used": 130000},
    },
    "Nothing": {
        "Phone (2a) Plus": {"new": 500000, "used": 200000},
        "Phone (2a)": {"new": 400000, "used": 160000},
        "Phone (2)": {"new": 600000, "used": 240000},
        "Phone (1)": {"new": 450000, "used": 170000},
    },
}

def is_iphone(brand: str) -> bool:
    return brand.lower() == "apple"

def get_iphone_biometric_type(model: str) -> str:
    if model in IPHONE_FACE_ID_MODELS:
        return "face_id"
    elif model in IPHONE_TOUCH_ID_MODELS:
        return "touch_id"
    return "face_id"

def get_reference_prices(brand: str, model: str) -> dict:
    brand_prices = REFERENCE_PRICES.get(brand, {})
    return brand_prices.get(model, {"new": None, "used": None})

def generate_access_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))

async def send_access_code_email(recipient_email: str, access_code: str, package_name: str, uses: int):
    """Send access code via email"""
    if not RESEND_API_KEY:
        logging.warning("Resend API key not configured, skipping email")
        return False
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding: 20px; background: #000; color: #fff;">
            <h1 style="margin: 0; font-size: 24px; letter-spacing: -1px;">STASHORRA</h1>
            <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Phone Price Estimator</p>
        </div>
        
        <div style="padding: 30px 20px; background: #f9f9f9;">
            <h2 style="color: #000; margin-top: 0;">Your Access Code is Ready!</h2>
            
            <p>Thank you for your payment. Here is your access code:</p>
            
            <div style="background: #000; color: #fff; padding: 20px; text-align: center; margin: 20px 0;">
                <span style="font-family: monospace; font-size: 32px; letter-spacing: 4px; font-weight: bold;">
                    {access_code}
                </span>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #666;">Package:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">{package_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #666;">Number of Uses:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: bold;">{uses} estimates</td>
                </tr>
            </table>
            
            <p style="color: #666; font-size: 14px;">
                Visit <a href="https://stashorra.store" style="color: #000;">stashorra.store</a> and enter your code to start getting price estimates.
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #888; font-size: 12px;">
            <p>&copy; 2025 Stashorra. Fair prices for everyone.</p>
            <p>Questions? Contact us at support@stashorra.store</p>
        </div>
    </div>
    """
    
    params = {
        "from": SENDER_EMAIL,
        "to": [recipient_email],
        "subject": f"Your Stashorra Access Code: {access_code}",
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Email sent to {recipient_email}, ID: {email.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

async def verify_access_code(code: str) -> dict:
    access_code = await db.access_codes.find_one({"code": code.upper()})
    if not access_code:
        return {"valid": False, "message": "Invalid access code"}
    
    if access_code.get("uses_remaining", 0) <= 0:
        return {"valid": False, "message": "Access code exhausted. Purchase a new one."}
    
    return {
        "valid": True,
        "uses_remaining": access_code.get("uses_remaining", 0),
        "message": "Access code valid"
    }

async def use_access_code(code: str) -> bool:
    result = await db.access_codes.update_one(
        {"code": code.upper(), "uses_remaining": {"$gt": 0}},
        {"$inc": {"uses_remaining": -1}, "$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
    )
    return result.modified_count > 0

async def scrape_jiji_prices(brand: str, model: str) -> List[PriceData]:
    prices = []
    try:
        search_query = f"{brand}+{model}".lower()
        url = f"https://jiji.ng/mobile-phones?query={search_query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
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
                                    prices.append(PriceData(source="market", price=price, currency="NGN"))
                    except:
                        continue
    except Exception as e:
        logging.error(f"Scraping error: {e}")
    return prices

async def estimate_price_with_ai(brand: str, model: str, condition: PhoneConditionExtended, new_price: Optional[float], used_price: Optional[float]) -> dict:
    if not EMERGENT_LLM_KEY:
        return calculate_fallback_estimate(brand, model, new_price, used_price, condition)
    
    try:
        from emergentintegrations.llm.openai import LlmChat
        
        if not new_price and not used_price:
            brand_prices = REFERENCE_PRICES.get(brand, {})
            if brand_prices:
                avg_new = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
                avg_used = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
                new_price = avg_new
                used_price = avg_used
            else:
                new_price = 200000
                used_price = 80000
        
        new_str = f"₦{new_price:,.0f}" if new_price else "₦200,000"
        used_str = f"₦{used_price:,.0f}" if used_price else "₦80,000"
        
        condition_str = f"Screen: {condition.screen_condition}, Body: {condition.body_condition}, Battery: {condition.battery_health}"
        if is_iphone(brand):
            bio_type = get_iphone_biometric_type(model)
            if bio_type == "face_id":
                condition_str += f", Face ID: {condition.face_id_working or 'yes'}"
            else:
                condition_str += f", Touch ID: {condition.touch_id_working or 'yes'}"
            condition_str += f", iCloud: {condition.icloud_status or 'unlocked'}"
        else:
            condition_str += f", FRP: {condition.frp_status or 'unlocked'}"

        prompt = f"""Estimate RESELLER BUYING PRICE for: {brand} {model}
New: {new_str}, Used market: {used_str}
Condition: {condition_str}

Rules: Reseller needs 20-30% margin. iCloud/FRP locked = major loss.
JSON only: {{"estimated_price": number, "confidence": "high/medium/low", "reasoning": "brief"}}"""

        llm_chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"p_{uuid.uuid4()}", system_message="Phone valuation expert.")
        response = await llm_chat.send_message(prompt)
        
        response_text = str(response.content if hasattr(response, 'content') else response).strip()
        if "```" in response_text:
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
        
        result = json.loads(response_text)
        return {"estimated_price": float(result.get("estimated_price", 0)), "confidence": result.get("confidence", "medium"), "reasoning": result.get("reasoning", "AI estimate.")}
    except Exception as e:
        logging.error(f"AI error: {e}")
        return calculate_fallback_estimate(brand, model, new_price, used_price, condition)

def calculate_fallback_estimate(brand: str, model: str, new_price: Optional[float], used_price: Optional[float], condition: PhoneConditionExtended) -> dict:
    if not new_price and not used_price:
        brand_prices = REFERENCE_PRICES.get(brand, {})
        if brand_prices:
            new_price = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
            used_price = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
        else:
            new_price, used_price = 200000, 80000
    
    screen = {"excellent": 1.0, "good": 0.88, "fair": 0.65, "cracked": 0.45}.get(condition.screen_condition, 0.7)
    body = {"excellent": 1.0, "good": 0.92, "fair": 0.8, "damaged": 0.55}.get(condition.body_condition, 0.8)
    battery = {"excellent": 1.0, "good": 0.88, "fair": 0.72, "poor": 0.55}.get(condition.battery_health, 0.8)
    
    if is_iphone(brand):
        bio_type = get_iphone_biometric_type(model)
        bio = {"yes": 1.0, "no": 0.6}.get(condition.face_id_working if bio_type == "face_id" else condition.touch_id_working or "yes", 1.0)
        icloud = {"unlocked": 1.0, "locked": 0.1}.get(condition.icloud_status or "unlocked", 1.0)
        overall = (screen + body + battery + bio + icloud) / 5
    else:
        frp = {"unlocked": 1.0, "locked": 0.3}.get(condition.frp_status or "unlocked", 1.0)
        overall = (screen + body + battery + frp) / 4
    
    base = used_price if used_price else (new_price * 0.45)
    estimated = base * overall
    
    return {"estimated_price": round(estimated, -3), "confidence": "medium" if new_price or used_price else "low", "reasoning": f"Condition score: {overall:.0%}. Reseller buying rate applied."}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Stashorra API"}

@api_router.get("/payment-info")
async def get_payment_info():
    return PAYMENT_INFO

@api_router.post("/verify-code")
async def verify_code(request: AccessCodeVerify):
    return await verify_access_code(request.code)

@api_router.get("/brands")
async def get_brands():
    return {"brands": ALL_BRANDS}

@api_router.get("/popular-phones")
async def get_popular_phones():
    brands = []
    for brand_name in ALL_BRANDS:
        models = list(REFERENCE_PRICES.get(brand_name, {}).keys())
        brand_type = "iphone" if brand_name == "Apple" else "android"
        brands.append({"name": brand_name, "models": models, "type": brand_type, "has_models": len(models) > 0})
    return {"brands": brands}

@api_router.get("/condition-questions/{brand}/{model}")
async def get_condition_questions_for_model(brand: str, model: str):
    common = [
        {"id": "screen_condition", "label": "Screen Condition", "description": "Check for cracks, scratches", "options": [{"value": "excellent", "label": "Excellent", "desc": "Perfect"}, {"value": "good", "label": "Good", "desc": "Minor scratches"}, {"value": "fair", "label": "Fair", "desc": "Visible issues"}, {"value": "cracked", "label": "Cracked", "desc": "Cracked"}]},
        {"id": "body_condition", "label": "Body Condition", "description": "Check for dents", "options": [{"value": "excellent", "label": "Excellent", "desc": "Like new"}, {"value": "good", "label": "Good", "desc": "Minor scuffs"}, {"value": "fair", "label": "Fair", "desc": "Visible dents"}, {"value": "damaged", "label": "Damaged", "desc": "Significant damage"}]},
        {"id": "battery_health", "label": "Battery Health", "description": "Check in settings", "options": [{"value": "excellent", "label": "90-100%", "desc": "Excellent"}, {"value": "good", "label": "80-89%", "desc": "Good"}, {"value": "fair", "label": "70-79%", "desc": "Fair"}, {"value": "poor", "label": "<70%", "desc": "Poor"}]},
        {"id": "speakers_working", "label": "Speakers", "description": "Test audio", "options": [{"value": "yes", "label": "Working", "desc": "Clear"}, {"value": "partial", "label": "Partial", "desc": "Issues"}, {"value": "no", "label": "Not Working", "desc": "Broken"}]},
        {"id": "cameras_working", "label": "Cameras", "description": "Test all cameras", "options": [{"value": "all_working", "label": "All Working", "desc": "Perfect"}, {"value": "front_only", "label": "Front Only", "desc": "Back issues"}, {"value": "back_only", "label": "Back Only", "desc": "Front issues"}, {"value": "issues", "label": "Issues", "desc": "Both broken"}]},
        {"id": "buttons_working", "label": "Buttons", "description": "Test buttons", "options": [{"value": "all_working", "label": "All Working", "desc": "Responsive"}, {"value": "some_issues", "label": "Some Issues", "desc": "Some sticky"}, {"value": "major_issues", "label": "Major Issues", "desc": "Not working"}]},
        {"id": "network_status", "label": "Network Lock", "description": "Is it unlocked?", "options": [{"value": "unlocked", "label": "Unlocked", "desc": "Any SIM"}, {"value": "locked_to_carrier", "label": "Locked", "desc": "Specific carrier"}]},
        {"id": "original_parts", "label": "Original Parts", "description": "All original?", "options": [{"value": "yes", "label": "All Original", "desc": "No replacements"}, {"value": "some_replaced", "label": "Some Replaced", "desc": "Screen/battery"}, {"value": "mostly_replaced", "label": "Mostly Replaced", "desc": "Multiple parts"}]}
    ]
    
    if is_iphone(brand):
        bio_type = get_iphone_biometric_type(model)
        iphone_qs = []
        if bio_type == "face_id":
            iphone_qs.append({"id": "face_id_working", "label": "Face ID", "description": "Test Face ID", "options": [{"value": "yes", "label": "Working", "desc": "Works"}, {"value": "no", "label": "Not Working", "desc": "Broken"}]})
        else:
            iphone_qs.append({"id": "touch_id_working", "label": "Touch ID", "description": "Test Touch ID", "options": [{"value": "yes", "label": "Working", "desc": "Works"}, {"value": "no", "label": "Not Working", "desc": "Broken"}]})
        iphone_qs.extend([
            {"id": "icloud_status", "label": "iCloud Status", "description": "CRITICAL: iCloud signed out?", "options": [{"value": "unlocked", "label": "Unlocked", "desc": "No iCloud"}, {"value": "locked", "label": "Locked", "desc": "Previous owner"}]},
            {"id": "back_glass_condition", "label": "Back Glass", "description": "Check back panel", "options": [{"value": "intact", "label": "Intact", "desc": "No cracks"}, {"value": "cracked", "label": "Cracked", "desc": "Cracked"}]},
            {"id": "true_tone_working", "label": "True Tone", "description": "In settings?", "options": [{"value": "yes", "label": "Working", "desc": "Available"}, {"value": "no", "label": "Not Working", "desc": "Disabled"}]}
        ])
        return {"questions": common + iphone_qs, "biometric_type": bio_type}
    else:
        android_qs = [
            {"id": "fingerprint_working", "label": "Fingerprint", "description": "Test sensor", "options": [{"value": "yes", "label": "Working", "desc": "Works"}, {"value": "no", "label": "Not Working", "desc": "Broken"}, {"value": "not_applicable", "label": "N/A", "desc": "No sensor"}]},
            {"id": "face_unlock_working", "label": "Face Unlock", "description": "Test face unlock", "options": [{"value": "yes", "label": "Working", "desc": "Works"}, {"value": "no", "label": "Not Working", "desc": "Broken"}, {"value": "not_applicable", "label": "N/A", "desc": "Not available"}]},
            {"id": "frp_status", "label": "FRP Status", "description": "CRITICAL: Google removed?", "options": [{"value": "unlocked", "label": "Unlocked", "desc": "No Google lock"}, {"value": "locked", "label": "Locked", "desc": "Previous account"}]},
            {"id": "charging_port", "label": "Charging Port", "description": "Test charging", "options": [{"value": "excellent", "label": "Excellent", "desc": "Perfect"}, {"value": "good", "label": "Good", "desc": "Minor wear"}, {"value": "loose", "label": "Loose", "desc": "Doesn't hold"}, {"value": "damaged", "label": "Damaged", "desc": "Issues"}]}
        ]
        return {"questions": common + android_qs, "biometric_type": "fingerprint"}

@api_router.post("/search-phone", response_model=ScrapedPrices)
async def search_phone_prices(request: PhoneSearchRequest):
    jiji_prices = await scrape_jiji_prices(request.brand, request.model)
    ref_prices = get_reference_prices(request.brand, request.model)
    
    new_prices, used_prices = [], jiji_prices if jiji_prices else []
    
    if ref_prices["new"]:
        new_prices = [PriceData(source="market", price=ref_prices["new"], currency="NGN")]
    if not used_prices and ref_prices["used"]:
        used_prices = [PriceData(source="market", price=ref_prices["used"], currency="NGN")]
    
    if not new_prices and not used_prices:
        brand_prices = REFERENCE_PRICES.get(request.brand, {})
        if brand_prices:
            avg_new = sum(p["new"] for p in brand_prices.values()) / len(brand_prices)
            avg_used = sum(p["used"] for p in brand_prices.values()) / len(brand_prices)
            new_prices = [PriceData(source="estimated", price=avg_new, currency="NGN")]
            used_prices = [PriceData(source="estimated", price=avg_used, currency="NGN")]
        else:
            new_prices = [PriceData(source="estimated", price=200000, currency="NGN")]
            used_prices = [PriceData(source="estimated", price=80000, currency="NGN")]
    
    return ScrapedPrices(new_prices=new_prices, used_prices=used_prices)

@api_router.post("/estimate-price", response_model=PriceEstimate)
async def estimate_price(request: PriceEstimateRequest):
    code_check = await verify_access_code(request.access_code)
    if not code_check["valid"]:
        raise HTTPException(status_code=403, detail=code_check["message"])
    
    if not await use_access_code(request.access_code):
        raise HTTPException(status_code=403, detail="Failed to use access code.")
    
    ai_result = await estimate_price_with_ai(request.brand, request.model, request.condition, request.new_price, request.used_price)
    
    estimate = PriceEstimate(brand=request.brand, model=request.model, condition=request.condition.model_dump(), new_price_avg=request.new_price, used_price_avg=request.used_price, estimated_price=ai_result["estimated_price"], confidence=ai_result["confidence"], reasoning=ai_result["reasoning"])
    
    doc = estimate.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    doc['access_code'] = request.access_code.upper()
    await db.estimates.insert_one(doc)
    
    return estimate

@api_router.get("/estimates")
async def get_estimates(limit: int = 10):
    return await db.estimates.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)

# Admin Routes
@api_router.post("/admin/login")
async def admin_login(request: AdminLogin):
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/admin/generate-code")
async def generate_code(request: AdminGenerateCode):
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    package = PAYMENT_PACKAGES.get(request.package, PAYMENT_PACKAGES["basic"])
    
    if request.package == "reseller":
        # Generate master code for reseller
        master_code = "R-" + generate_access_code()
        while await db.reseller_masters.find_one({"master_code": master_code}):
            master_code = "R-" + generate_access_code()
        
        # Generate 20 individual codes for reseller to distribute
        sub_codes = []
        codes_count = package.get("codes_count", 20)
        uses_per_code = package.get("uses_per_code", 1)
        
        for i in range(codes_count):
            sub_code = generate_access_code()
            while await db.access_codes.find_one({"code": sub_code}) or sub_code in [c["code"] for c in sub_codes]:
                sub_code = generate_access_code()
            
            sub_code_doc = {
                "code": sub_code,
                "uses_remaining": uses_per_code,
                "package": "reseller_sub",
                "master_code": master_code,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "note": f"Reseller code #{i+1}",
                "last_used": None,
                "distributed": False
            }
            sub_codes.append(sub_code_doc)
        
        # Insert all sub codes
        if sub_codes:
            await db.access_codes.insert_many(sub_codes)
        
        # Create master record
        master_doc = {
            "master_code": master_code,
            "package": "reseller",
            "codes_count": codes_count,
            "note": request.note or "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.reseller_masters.insert_one(master_doc)
        
        email_sent = False
        if request.send_email and request.recipient_email:
            email_sent = await send_reseller_code_email(request.recipient_email, master_code, codes_count)
        
        return {
            "code": master_code,
            "is_reseller": True,
            "codes_count": codes_count,
            "package": package["name"],
            "email_sent": email_sent
        }
    else:
        # Basic package - single code with multiple uses
        code = generate_access_code()
        while await db.access_codes.find_one({"code": code}):
            code = generate_access_code()
        
        doc = {
            "code": code,
            "uses_remaining": package["uses"],
            "package": request.package,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "note": request.note or "",
            "last_used": None
        }
        await db.access_codes.insert_one(doc)
        
        email_sent = False
        if request.send_email and request.recipient_email:
            email_sent = await send_access_code_email(request.recipient_email, code, package["name"], package["uses"])
        
        return {"code": code, "uses": package["uses"], "package": package["name"], "email_sent": email_sent}

async def send_reseller_code_email(recipient_email: str, master_code: str, codes_count: int):
    """Send reseller master code via email"""
    if not RESEND_API_KEY:
        return False
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding: 20px; background: #000; color: #fff;">
            <h1 style="margin: 0; font-size: 24px;">STASHORRA</h1>
            <p style="margin: 5px 0 0 0; font-size: 12px; color: #888;">Reseller Dashboard</p>
        </div>
        <div style="padding: 30px 20px; background: #f9f9f9;">
            <h2 style="color: #000;">Your Reseller Code is Ready!</h2>
            <div style="background: #22c55e; color: #fff; padding: 20px; text-align: center; margin: 20px 0;">
                <span style="font-family: monospace; font-size: 28px; letter-spacing: 4px; font-weight: bold;">{master_code}</span>
            </div>
            <p><strong>{codes_count} individual codes</strong> are ready for you to distribute!</p>
            <p>Visit stashorra.store and click the <strong>👁 (eye icon)</strong> button, then enter your master code to access your reseller dashboard.</p>
        </div>
    </div>
    """
    
    params = {
        "from": SENDER_EMAIL,
        "to": [recipient_email],
        "subject": f"Your Stashorra Reseller Code: {master_code}",
        "html": html_content
    }
    
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except:
        return False

@api_router.post("/reseller/dashboard")
async def get_reseller_dashboard(request: ResellerDashboardRequest):
    """Get reseller's codes dashboard"""
    master_code = request.master_code.upper()
    
    # Check if it's a valid reseller master code
    master = await db.reseller_masters.find_one({"master_code": master_code}, {"_id": 0})
    if not master:
        raise HTTPException(status_code=404, detail="Invalid reseller code")
    
    # Get all sub-codes for this reseller
    sub_codes = await db.access_codes.find(
        {"master_code": master_code},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Calculate stats
    total_codes = len(sub_codes)
    available_codes = len([c for c in sub_codes if c.get("uses_remaining", 0) > 0])
    used_codes = total_codes - available_codes
    
    return {
        "master_code": master_code,
        "note": master.get("note", ""),
        "created_at": master.get("created_at"),
        "total_codes": total_codes,
        "available_codes": available_codes,
        "used_codes": used_codes,
        "codes": sub_codes
    }

@api_router.get("/admin/reseller-masters")
async def get_reseller_masters(username: str, password: str):
    """Get all reseller master codes"""
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    masters = await db.reseller_masters.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Add stats to each master
    for master in masters:
        sub_codes = await db.access_codes.find({"master_code": master["master_code"]}).to_list(100)
        master["total_codes"] = len(sub_codes)
        master["available_codes"] = len([c for c in sub_codes if c.get("uses_remaining", 0) > 0])
    
    return {"masters": masters}

@api_router.get("/admin/codes")
async def get_all_codes(username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"codes": await db.access_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)}

@api_router.delete("/admin/code/{code}")
async def delete_code(code: str, username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    result = await db.access_codes.delete_one({"code": code.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Code not found")
    return {"message": "Deleted"}

app.include_router(api_router)

app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])

logging.basicConfig(level=logging.INFO)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
