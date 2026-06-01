# Changelog

All notable changes to Infinite Craft will be documented in this file.

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
