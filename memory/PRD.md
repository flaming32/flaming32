# Stashorra - Phone Price Estimator PRD

## Original Problem Statement
Build a phone estimated price calculator app. Use AI to give a rough estimate after analyzing the condition of the phone. Prices should reflect what a reseller would pay (lower because they need profit margin and repair costs).

## Latest Updates (December 2025)
- 78 brands alphabetically sorted with search functionality
- Custom model input for phones not in database
- iPhone biometric detection: Touch ID for iPhone 8 and older, Face ID for iPhone X and newer
- Android: fingerprint + face unlock questions
- Lower, realistic reseller buying prices
- Removed data source labels from UI

## User Personas
1. **Phone Sellers** - People selling used phones who need fair reseller pricing
2. **Phone Buyers** - People verifying prices before buying used
3. **Phone Resellers** - Business owners who trade phones

## All 78 Brands (Alphabetically)
AGM, Alcatel, Allview, Apple, Archos, Asus, Asus ROG, BQ, Benco, Black Shark, Blackview, Blu, Cat, Cherry Mobile, Condor, Coolpad, Doogee, Doro, Energizer, Essential, Fairphone, Fujitsu, General Mobile, Gionee, Google, Google Pixel, HMD, HMD Global, HTC, Hisense, Honor, Huawei, Infinix, Inoi, Intex, Itel, iQOO, Kyocera, LG, Lava, LeEco, Lenovo, Maxwest, Meizu, Micromax, Motorola, NEC, Nokia, Nubia, OnePlus, Oppo, Palm, Panasonic, Philips, Poco, Prestigio, QMobile, Razer, Realme, Redmi, Samsung, Sharp, Sico, Sony, Symphony, TCL, Tecno, Transsion, Ulefone, Umidigi, Vertu, Vivo, Vsmart, Wiko, Xiaomi, ZTE, ZUK, myPhone

## iPhone Biometric Detection
- **Face ID models**: iPhone X, XS, XS Max, XR, 11 series, 12 series, 13 series, 14 series, 15 series
- **Touch ID models**: iPhone SE (all), iPhone 8/8 Plus, iPhone 7/7 Plus, iPhone 6s/6s Plus, iPhone 6/6 Plus

## Condition Assessment

### iPhone Questions (12 total)
1. Screen Condition
2. Body/Frame Condition  
3. Battery Health
4. Speakers & Earpiece
5. Cameras
6. Physical Buttons
7. Network Lock Status
8. Original Parts
9. **Face ID OR Touch ID** (based on model)
10. **iCloud Lock Status** (CRITICAL)
11. Back Glass
12. True Tone Display

### Android Questions (12 total)
1. Screen Condition
2. Body/Frame Condition
3. Battery Health
4. Speakers & Earpiece
5. Cameras
6. Physical Buttons
7. Network Lock Status
8. Original Parts
9. **Fingerprint Sensor**
10. **Face Unlock**
11. **FRP (Google Lock) Status** (CRITICAL)
12. Charging Port Condition

## Pricing Philosophy
- Prices reflect **RESELLER BUYING PRICE** (what a vendor would pay)
- Resellers need 20-30% profit margin + repair costs
- Used phones: ~40-50% of new price for good condition
- iCloud locked = 90% value loss
- FRP locked = 70% value loss
- Cracked screen = 40-50% reduction
- Poor battery = 25-35% reduction
- Non-working biometrics = 30-40% reduction

## Features Implemented
- [x] 78 brands with search functionality
- [x] Custom model input (+ button)
- [x] Model search within brand
- [x] Biometric detection by iPhone model
- [x] Face Unlock question for Android
- [x] Realistic reseller pricing
- [x] AI-powered estimation
- [x] Receipt-style results

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + Motor (async MongoDB)
- **AI**: OpenAI via Emergent Integrations

## API Endpoints
- `GET /api/brands` - All 78 brands
- `GET /api/popular-phones` - Brands with known models
- `GET /api/condition-questions/{brand}/{model}` - Dynamic questions
- `POST /api/search-phone` - Fetch prices
- `POST /api/estimate-price` - AI estimation
- `GET /api/estimates` - History

## Next Tasks
1. Add more models to reference database
2. User accounts for saved estimates
3. Price history tracking
