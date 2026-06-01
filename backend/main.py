from typing import Optional
import json
import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

AI_CACHE: dict[str, dict] = {}

EMOJI_MAP = {
    "water": "💧", "fire": "🔥", "earth": "🌍", "wind": "💨",
    "steam": "♨️", "mud": "💩", "wave": "🌊", "lava": "🌋",
    "smoke": "💨", "dust": "✨", "cloud": "☁️", "rain": "🌧️",
    "thunder": "⚡", "plant": "🌱", "tree": "🌳", "forest": "🌲",
    "obsidian": "⬛", "mountain": "⛰️", "volcano": "🌋",
    "brick": "🧱", "wall": "🧱", "house": "🏠", "garden": "🏡",
    "island": "🏝️", "ocean": "🌊", "fog": "🌫️", "ash": "🌫️",
    "algae": "🌿", "soil": "🌾", "gunpowder": "💥",
    "sand": "🏖️", "glass": "🔮", "metal": "🔩", "stone": "🪨",
    "mountain range": "🏔️",
}

def get_emoji(name: str) -> str:
    key = name.lower()
    return EMOJI_MAP.get(key, "🔹")

def normalize(name: str) -> str:
    if not isinstance(name, str):
        name = str(name)
    return re.sub(r'[^\w\s]', '', name.lower().strip().replace('the ', '').replace('a ', '').replace('an ', ''))

def make_cache_key(first: str, second: str) -> str:
    a, b = normalize(first), normalize(second)
    return f"{a}:{b}" if a <= b else f"{b}:{a}"

STATIC_RECIPES = {
    make_cache_key("earth", "fire"): {"name": "Lava", "emoji": "🌋"},
    make_cache_key("water", "fire"): {"name": "Steam", "emoji": "♨️"},
    make_cache_key("water", "earth"): {"name": "Mud", "emoji": "💩"},
    make_cache_key("water", "wind"): {"name": "Wave", "emoji": "🌊"},
    make_cache_key("earth", "wind"): {"name": "Dust", "emoji": "✨"},
    make_cache_key("fire", "wind"): {"name": "Smoke", "emoji": "💨"},
    make_cache_key("steam", "wind"): {"name": "Cloud", "emoji": "☁️"},
    make_cache_key("cloud", "water"): {"name": "Rain", "emoji": "🌧️"},
    make_cache_key("cloud", "fire"): {"name": "Thunder", "emoji": "⚡"},
    make_cache_key("rain", "earth"): {"name": "Plant", "emoji": "🌱"},
    make_cache_key("plant", "earth"): {"name": "Tree", "emoji": "🌳"},
    make_cache_key("tree", "fire"): {"name": "Ash", "emoji": "🌫️"},
    make_cache_key("mud", "fire"): {"name": "Brick", "emoji": "🧱"},
    make_cache_key("lava", "water"): {"name": "Obsidian", "emoji": "⬛"},
    make_cache_key("dust", "fire"): {"name": "Gunpowder", "emoji": "💥"},
    make_cache_key("brick", "brick"): {"name": "Wall", "emoji": "🧱"},
    make_cache_key("wall", "wall"): {"name": "House", "emoji": "🏠"},
    make_cache_key("house", "plant"): {"name": "Garden", "emoji": "🏡"},
    make_cache_key("wave", "earth"): {"name": "Island", "emoji": "🏝️"},
    make_cache_key("wave", "wave"): {"name": "Ocean", "emoji": "🌊"},
    make_cache_key("tree", "tree"): {"name": "Forest", "emoji": "🌲"},
    make_cache_key("plant", "plant"): {"name": "Forest", "emoji": "🌲"},
    make_cache_key("plant", "water"): {"name": "Algae", "emoji": "🌿"},
    make_cache_key("ash", "water"): {"name": "Mud", "emoji": "💩"},
    make_cache_key("obsidian", "earth"): {"name": "Mountain", "emoji": "⛰️"},
    make_cache_key("rain", "fire"): {"name": "Thunder", "emoji": "⚡"},
    make_cache_key("lava", "earth"): {"name": "Volcano", "emoji": "🌋"},
    make_cache_key("dust", "water"): {"name": "Mud", "emoji": "💩"},
    make_cache_key("mud", "wind"): {"name": "Dust", "emoji": "✨"},
    make_cache_key("human", "house"): {"name": "Home", "emoji": "🏠"},
    make_cache_key("tree", "human"): {"name": "Wood", "emoji": "🪵"},
    make_cache_key("wood", "fire"): {"name": "Ash", "emoji": "🌫️"},
    make_cache_key("stone", "water"): {"name": "Sand", "emoji": "🏖️"},
    make_cache_key("sand", "fire"): {"name": "Glass", "emoji": "🔮"},
    make_cache_key("metal", "fire"): {"name": "Blade", "emoji": "🔪"},
    make_cache_key("ocean", "earth"): {"name": "Island", "emoji": "🏝️"},
    make_cache_key("ocean", "fire"): {"name": "Fog", "emoji": "🌫️"},
    make_cache_key("mountain", "mountain"): {"name": "Mountain Range", "emoji": "🏔️"},
    make_cache_key("ash", "earth"): {"name": "Soil", "emoji": "🌾"},
    make_cache_key("rain", "water"): {"name": "Flood", "emoji": "🌊"},
    make_cache_key("rain", "wind"): {"name": "Storm", "emoji": "⛈️"},
    make_cache_key("cloud", "cloud"): {"name": "Sky", "emoji": "☁️"},
    make_cache_key("cloud", "earth"): {"name": "Fog", "emoji": "🌫️"},
    make_cache_key("fire", "fire"): {"name": "Flame", "emoji": "🔥"},
    make_cache_key("water", "water"): {"name": "Puddle", "emoji": "💧"},
    make_cache_key("earth", "earth"): {"name": "Soil", "emoji": "🌾"},
    make_cache_key("wind", "wind"): {"name": "Tornado", "emoji": "🌪️"},
}

def make_response(name: str, emoji: str) -> dict:
    return {"name": name, "emoji": emoji, "id": normalize(name)}

class CombineRequest(BaseModel):
    first: str
    second: str

SYSTEM_PROMPT = """You are an element combination engine for a crafting game. Given two elements, return what they would create when combined.

Rules:
- Be creative but logical
- Return ONLY a JSON object with exactly these fields: "name" (string) and "emoji" (single emoji)
- Do not include any text before or after the JSON
- The emoji should be relevant to the result
- Keep names short (1-3 words max)
- Example output: {"name": "Steam", "emoji": "♨️"}"""

@app.post("/api/combine")
async def combine(req: CombineRequest):
    if not API_KEY or API_KEY == "sk-or-v1-":
        raise HTTPException(status_code=500, detail="API key not configured")

    cache_key = make_cache_key(req.first, req.second)

    # 1. Check static recipes (instant)
    if cache_key in STATIC_RECIPES:
        r = STATIC_RECIPES[cache_key]
        return make_response(r["name"], r["emoji"])

    # 2. Check AI cache (instant for previously discovered combos)
    if cache_key in AI_CACHE:
        return AI_CACHE[cache_key]

    # 3. Call AI (slow, but cached for next time)
    for attempt in range(2):
        try:
            async with AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "Infinite Craft",
                    },
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Combine: {req.first} + {req.second}. Return only JSON like {{\"name\": \"Something\", \"emoji\": \"🔹\"}}"},
                        ],
                        "temperature": 0.5,
                        "max_tokens": 50,
                    },
                    timeout=15.0,
                )

            data = resp.json()

            if "error" in data:
                if attempt < 1:
                    continue
                return make_response("Unknown", "🔹")

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content or not isinstance(content, str):
                if attempt < 1:
                    continue
                return make_response("Unknown", "🔹")

            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)

            raw_name = result.get("name")
            name = str(raw_name) if raw_name is not None and raw_name != "" else "Unknown"
            emoji = result.get("emoji", "")
            if not emoji or not isinstance(emoji, str) or len(emoji) > 4:
                emoji = get_emoji(name)

            response = make_response(name, emoji)
            AI_CACHE[cache_key] = response
            return response

        except (json.JSONDecodeError, KeyError):
            if attempt < 1:
                continue
        except Exception:
            if attempt < 1:
                continue

    return make_response("Unknown", "🔹")

@app.get("/api/health")
async def health():
    return {"status": "ok", "cached": len(AI_CACHE)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
