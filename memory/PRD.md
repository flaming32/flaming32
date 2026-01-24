# Stashorra - Phone Price Estimator PRD

## Original Problem Statement
Build a phone estimated price calculator app using information of a brand new one comparing it to the used version. Then use AI to give a rough estimate after analyzing the information given by the user about the condition of the phone.

## User Choices & Updates
- AI Integration: Emergent LLM key (OpenAI)
- Data Sources: Jiji.ng for iPhone used prices, Slot.ng for Android new prices
- Condition Input: Comprehensive (13 questions for iPhone, 11 for Android)
- Theme: Black and white
- Logo: "Stashorra" text
- Remove data source labels from UI

## User Personas
1. **Phone Sellers** - People wanting to sell their used phones and need fair pricing
2. **Phone Buyers** - People looking to buy used phones and want to verify prices
3. **Phone Traders** - Business owners who trade phones regularly

## Core Requirements
- Phone brand/model selection from 12 major brands (165+ models)
- Price comparison between new and used markets
- Detailed condition assessment based on phone type
- AI-powered price estimation
- Receipt-style result display

## What's Been Implemented (December 2025)

### Brands & Models (165+ total)
- Apple (25 models) - iPhone 15 Pro Max down to iPhone SE
- Samsung (23 models) - Galaxy S24 Ultra to Galaxy A04
- Tecno (21 models) - Phantom X2 to Pop 7
- Infinix (16 models) - Zero 30 to Smart 7
- Itel (11 models) - S24 to A50
- Xiaomi (20 models) - 14 Ultra to POCO C65
- Google (9 models) - Pixel 8 Pro to Pixel 6a
- OnePlus (7 models) - 12 to Nord N30
- Oppo (11 models) - Find X7 Ultra to A18
- Vivo (8 models) - X100 Pro to Y27
- Realme (9 models) - GT 5 Pro to Note 50
- Nokia (5 models) - G42 to C12

### iPhone Assessment (13 Questions)
1. Screen Condition
2. Body/Frame Condition
3. Battery Health
4. Speakers & Earpiece
5. Cameras
6. Physical Buttons
7. Network Lock Status
8. Original Parts
9. **Face ID** (critical for value)
10. **Touch ID**
11. **iCloud Lock Status** (CRITICAL - locked = major value loss)
12. **Back Glass**
13. **True Tone Display**

### Android Assessment (11 Questions)
1. Screen Condition
2. Body/Frame Condition
3. Battery Health
4. Speakers & Earpiece
5. Cameras
6. Physical Buttons
7. Network Lock Status
8. Original Parts
9. **Fingerprint Sensor**
10. **FRP (Google Lock) Status** (CRITICAL - locked = major value loss)
11. **Charging Port Condition**

### Features Implemented
- [x] Dynamic condition questions based on phone type
- [x] AI price estimation with detailed condition analysis
- [x] Receipt-style results page
- [x] Condition report with color-coded status
- [x] Share functionality
- [x] Mobile responsive design
- [x] Progress indicator during assessment

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + Motor (async MongoDB)
- **AI**: OpenAI via Emergent Integrations
- **Data**: Reference prices (165+ phone models)

## API Endpoints
- `GET /api/popular-phones` - Returns 12 brands with type info
- `GET /api/condition-questions/{brand}` - Dynamic questions
- `POST /api/search-phone` - Fetches price references
- `POST /api/estimate-price` - AI-powered estimation
- `GET /api/estimates` - Estimate history

## Valuation Rules (Built into AI)
1. Used phones ALWAYS priced lower than new
2. iCloud locked iPhones lose 60-70% value
3. Cracked screens reduce value by 30-50%
4. Poor battery (<70%) reduces value by 20-30%
5. Non-working Face ID/Touch ID reduces iPhone value by 25-35%
6. FRP locked Androids lose 40-50% value
7. Non-original parts reduce value by 15-25%

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] 12 brands with 165+ models
- [x] iPhone-specific questions (13)
- [x] Android-specific questions (11)
- [x] AI estimation with detailed condition

### P1 (Important)
- [ ] Live web scraping when sites allow
- [ ] Price history tracking
- [ ] User authentication

### P2 (Nice to Have)
- [ ] Image upload for condition assessment
- [ ] Price trend charts
- [ ] Multi-language support

## Next Tasks
1. Add more models as new phones release
2. Implement user accounts
3. Add price trend visualization
