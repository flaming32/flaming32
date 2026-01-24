# Stashorra - Phone Price Estimator PRD

## Original Problem Statement
Build a phone estimated price calculator app using information of a brand new one on slot.com comparing it to the used version on jiji.com. Then use AI to give a rough estimate after analyzing the information given by the user about the condition of the phone.

## User Choices
- AI Integration: Emergent LLM key (OpenAI)
- Data Source: Web scraping with reference prices fallback
- Condition Input: Basic (screen, battery, physical damage)
- Theme: Black and white
- Logo: "Stashorra" text

## User Personas
1. **Phone Sellers** - People wanting to sell their used phones and need fair pricing
2. **Phone Buyers** - People looking to buy used phones and want to verify prices
3. **Phone Traders** - Business owners who trade phones regularly

## Core Requirements (Static)
- Phone brand/model selection from popular devices
- Price comparison between new (Slot.ng) and used (Jiji.ng) markets
- Condition assessment: Screen, Battery Health, Physical Damage
- AI-powered price estimation
- Receipt-style result display

## What's Been Implemented (December 2025)
- [x] Landing page with "WHAT IS IT WORTH?" headline
- [x] Phone selection (6 brands, 40+ models)
- [x] Web scraping for Slot.ng and Jiji.ng (with reference price fallback)
- [x] 3-step condition assessment form
- [x] AI price estimation using Emergent LLM key
- [x] Receipt-style results page
- [x] Share functionality
- [x] Black & white theme with Syne/Chivo/JetBrains Mono fonts
- [x] MongoDB storage for estimates

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + Motor (async MongoDB)
- **AI**: OpenAI via Emergent Integrations
- **Scraping**: httpx + BeautifulSoup4 (with reference data fallback)

## API Endpoints
- `GET /api/popular-phones` - Returns supported phone brands/models
- `POST /api/search-phone` - Scrapes prices from Slot.ng and Jiji.ng
- `POST /api/estimate-price` - Calculates AI-powered price estimate
- `GET /api/estimates` - Returns estimate history

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Core price estimation flow
- [x] AI integration
- [x] Reference prices for common phones

### P1 (Important)
- [ ] Enable live web scraping when sites allow
- [ ] Add more phone brands/models
- [ ] User authentication for saving estimates
- [ ] Price history tracking

### P2 (Nice to Have)
- [ ] Image upload for condition assessment
- [ ] Price trend charts
- [ ] Email/SMS quote delivery
- [ ] Multi-language support (Pidgin, Yoruba, etc.)

## Next Tasks
1. Expand phone database with more models
2. Add price trend visualization
3. Implement user accounts for saved estimates
