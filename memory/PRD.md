# Stashorra - Phone Price Estimator PRD

## Original Problem Statement
Build a phone estimated price calculator app using AI to estimate reseller buying prices based on phone condition. Compare new price (slot.com) with used price (jiji.com). Business name: "Stashorra".

## Core Requirements
- Extensive, searchable list of phone brands and models
- Differentiated evaluation questions (iPhone vs Android, Face ID vs Touch ID)
- Payment system: users pay ₦400 for 2 uses to get an access code
- Admin panel (/admin) to generate access codes
- Reseller Package: master code unlocks 20 sub-codes to distribute
- AI-powered estimate for custom models
- Email notifications when payment is made
- Light/dark mode toggle

## Payment System
- Price: ₦400 for 2 price estimates
- Bank: KUDA MFB
- Account: 3002978669
- Name: STASHORRA STORE
- Email: support@stashorra.store

## Admin Panel
- URL: /admin
- Login: admin / Olaoluwa32$
- Features: Generate access codes, view all codes, delete codes, track usage, generate reseller codes

## Features Implemented
- [x] 78 brands with searchable combobox (Popover+Command pattern)
- [x] Samsung: 98 models (S, A, Note, Z, M, F, J series)
- [x] Custom model input (inside dropdown)
- [x] iPhone biometric detection (Face ID vs Touch ID by model)
- [x] Android-specific questions (fingerprint, FRP, charging port)
- [x] AI-powered price estimation (OpenAI via Emergent)
- [x] Payment modal with bank details
- [x] Access code verification
- [x] Uses remaining display
- [x] Admin panel with secure login
- [x] Reseller package (master code + 20 sub-codes)
- [x] Reseller dashboard modal (view/copy sub-codes)
- [x] Light/dark mode toggle
- [x] Check uses balance feature

## API Endpoints
- GET /api/payment-info
- POST /api/verify-code
- GET /api/brands
- GET /api/popular-phones
- GET /api/condition-questions/{brand}/{model}
- POST /api/search-phone
- POST /api/estimate-price (requires access code)
- POST /api/admin/login
- POST /api/admin/generate-code
- GET /api/admin/codes
- DELETE /api/admin/code/{code}
- POST /api/admin/generate-reseller-code
- POST /api/reseller/dashboard
- GET /api/admin/reseller-masters

## Architecture
- Frontend: React + Tailwind CSS + Shadcn/UI + Framer Motion
- Backend: FastAPI + Motor (async MongoDB)
- AI: OpenAI via Emergent Integrations
- Auth: Access codes stored in MongoDB

## DB Collections
- access_codes: {code, uses_left, is_reseller_master, master_code, created_at, package, email_sent}
- reseller_masters: master codes with stats

## Next Tasks (Priority Order)
1. P1: Email notifications via Resend (needs API key from user)
2. P2: Populate more phone models for other brands
3. P3: AI logic for custom model estimation (backend)
4. Future: Bulk upload for resellers
5. Future: Price alerts
6. Future: Backend refactoring (modularize server.py)

## Known Limitations
- Web scraping (Slot.com / Jiji.com) is MOCKED with static reference prices
- Many brands besides Samsung still lack models
