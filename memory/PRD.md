# Stashorra - Phone Price Estimator PRD

## Original Problem Statement
Build a phone estimated price calculator app using AI to estimate reseller buying prices based on phone condition.

## Latest Updates (December 2025)

### Payment System
- **Price**: ₦400 for 2 price estimates
- **Bank**: KUDA MFB
- **Account**: 3002978669
- **Name**: STASHORRA STORE
- **Email**: support@stashorra.store

### Admin Panel
- **URL**: /admin
- **Login**: admin / Olaoluwa32$
- Features: Generate access codes, view all codes, delete codes, track usage

### Access Code System
- Users must have valid access code to get estimates
- Each code allows 2 estimates
- Codes are 8-character alphanumeric
- Usage tracked and decremented per estimate

## All 78 Brands (Alphabetically)
AGM, Alcatel, Allview, Apple, Archos, Asus, Asus ROG, BQ, Benco, Black Shark, Blackview, Blu, Cat, Cherry Mobile, Condor, Coolpad, Doogee, Doro, Energizer, Essential, Fairphone, Fujitsu, General Mobile, Gionee, Google, Google Pixel, HMD, HMD Global, HTC, Hisense, Honor, Huawei, Infinix, Inoi, Intex, Itel, iQOO, Kyocera, LG, Lava, LeEco, Lenovo, Maxwest, Meizu, Micromax, Motorola, NEC, Nokia, Nubia, OnePlus, Oppo, Palm, Panasonic, Philips, Poco, Prestigio, QMobile, Razer, Realme, Redmi, Samsung, Sharp, Sico, Sony, Symphony, TCL, Tecno, Transsion, Ulefone, Umidigi, Vertu, Vivo, Vsmart, Wiko, Xiaomi, ZTE, ZUK, myPhone

## Features Implemented

### User Features
- [x] 78 brands with search functionality
- [x] Custom model input (inside dropdown)
- [x] iPhone biometric detection (Face ID vs Touch ID by model)
- [x] Android-specific questions (fingerprint, FRP, charging port)
- [x] AI-powered price estimation for unknown phones
- [x] Payment modal with bank details
- [x] Access code verification
- [x] Uses remaining display

### Admin Features
- [x] Secure login (admin/Olaoluwa32$)
- [x] Generate access codes
- [x] View all codes with usage stats
- [x] Copy codes to clipboard
- [x] Delete codes
- [x] Dashboard stats (total codes, active codes, uses left)

## API Endpoints
- `GET /api/payment-info` - Payment details
- `POST /api/verify-code` - Verify access code
- `GET /api/brands` - All 78 brands
- `GET /api/popular-phones` - Brands with models
- `GET /api/condition-questions/{brand}/{model}` - Dynamic questions
- `POST /api/search-phone` - Fetch prices
- `POST /api/estimate-price` - AI estimation (requires access code)
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/generate-code` - Generate access code
- `GET /api/admin/codes` - List all codes
- `DELETE /api/admin/code/{code}` - Delete code

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + Motor (async MongoDB)
- **AI**: OpenAI via Emergent Integrations
- **Auth**: Access codes stored in MongoDB

## Next Tasks
1. Add email notification when code is generated
2. Add payment verification integration
3. Add bulk code generation for resellers
