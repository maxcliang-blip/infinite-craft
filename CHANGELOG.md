# Changelog

All notable changes to Infinite Craft will be documented in this file.

## [1.2.1] - 2026-06-03

### Emoji Fixes
- Expanded emoji map to 400+ items with correct emoji assignments
- EMOJI_MAP entries now always override AI-provided emojis
- Added validation to reject person emojis for non-human items
- Fallback emojis now use the curated map instead of 🔹

## [1.2.0] - 2026-06-03

### Ollama Integration
- Replaced OpenRouter with local Ollama for AI inference
- No more rate limits — always available
- Running qwen2.5:7b model on VPS (CPU inference)
- Faster, more consistent responses
- Removed dependency on external API keys

## [1.1.1] - 2026-06-02

### AI Improvements
- Enhanced system prompt for more creative and logical item combinations
- AI now considers real-world reactions, abstract connections, and cause-and-effect
- Better progression: simple combos → complex items, complex combos → surprising results
- Increased temperature (0.5 → 0.7) for more variety in results
- Increased max tokens (50 → 80) for richer responses

## [1.1.0] - 2026-06-02

### Added
- Sidebar search bar to filter discovered elements
- Local storage persistence — discovered elements saved across browser sessions
- Changelog modal accessible from header button

### Fixed
- API calls working on all computers via Cloudflare tunnel (HTTPS)
- Frontend now deployed directly on VPS alongside backend to avoid mixed-content issues
- Build configuration for GitHub Pages deployment

### Infrastructure
- Cloudflare tunnel for HTTPS access to backend (no domain required)
- Automated GitHub Pages deployment workflow
- Frontend served from same VPS as backend via nginx proxy

## [1.0.0] - 2026-06-01

### Initial Release

#### Frontend
- React + TypeScript app built with Vite
- Drag-and-drop elements from sidebar to workspace
- Drag elements on canvas to combine them (proximity detection)
- Double-click to duplicate elements
- Collapsible sidebar with element count
- Discovery counter showing found elements
- Clean, minimal UI inspired by the original Infinite Craft

#### Backend
- FastAPI backend deployed on VPS (port 80 via nginx reverse proxy)
- OpenRouter AI integration for dynamic element generation
- SQLite database for persistent recipe caching
- 47 static recipes for instant responses on common combinations
- AI results cached in DB — subsequent combos are instant
- Automatic emoji generation and name normalization

#### Deployment
- Frontend: GitHub Pages
- Backend: Oracle Cloud VPS with systemd service + nginx
- Deploy script for quick backend updates
- CORS enabled for frontend-to-backend communication

#### Game Features
- 4 base elements: Water, Fire, Earth, Wind
- 47 predefined static recipes
- AI-powered infinite combinations
- Element discovery tracking
