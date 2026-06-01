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
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")

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

STATIC_RECIPES = {
    ("earth", "fire"): {"name": "Lava", "emoji": "🌋"},
    ("water", "fire"): {"name": "Steam", "emoji": "♨️"},
    ("water", "earth"): {"name": "Mud", "emoji": "💩"},
    ("water", "wind"): {"name": "Wave", "emoji": "🌊"},
    ("earth", "wind"): {"name": "Dust", "emoji": "✨"},
    ("fire", "wind"): {"name": "Smoke", "emoji": "💨"},
    ("steam", "wind"): {"name": "Cloud", "emoji": "☁️"},
    ("cloud", "water"): {"name": "Rain", "emoji": "🌧️"},
    ("cloud", "fire"): {"name": "Thunder", "emoji": "⚡"},
    ("rain", "earth"): {"name": "Plant", "emoji": "🌱"},
    ("plant", "earth"): {"name": "Tree", "emoji": "🌳"},
    ("tree", "fire"): {"name": "Ash", "emoji": "🌫️"},
    ("mud", "fire"): {"name": "Brick", "emoji": "🧱"},
    ("lava", "water"): {"name": "Obsidian", "emoji": "⬛"},
    ("dust", "fire"): {"name": "Gunpowder", "emoji": "💥"},
    ("brick", "brick"): {"name": "Wall", "emoji": "🧱"},
    ("wall", "wall"): {"name": "House", "emoji": "🏠"},
    ("house", "plant"): {"name": "Garden", "emoji": "🏡"},
    ("wave", "earth"): {"name": "Island", "emoji": "🏝️"},
    ("wave", "wave"): {"name": "Ocean", "emoji": "🌊"},
    ("tree", "tree"): {"name": "Forest", "emoji": "🌲"},
    ("plant", "plant"): {"name": "Forest", "emoji": "🌲"},
    ("plant", "water"): {"name": "Algae", "emoji": "🌿"},
    ("ash", "water"): {"name": "Mud", "emoji": "💩"},
    ("obsidian", "earth"): {"name": "Mountain", "emoji": "⛰️"},
    ("rain", "fire"): {"name": "Thunder", "emoji": "⚡"},
    ("lava", "earth"): {"name": "Volcano", "emoji": "🌋"},
    ("dust", "water"): {"name": "Mud", "emoji": "💩"},
    ("mud", "wind"): {"name": "Dust", "emoji": "✨"},
    ("human", "house"): {"name": "Home", "emoji": "🏠"},
    ("tree", "human"): {"name": "Wood", "emoji": "🪵"},
    ("wood", "fire"): {"name": "Ash", "emoji": "🌫️"},
    ("stone", "water"): {"name": "Sand", "emoji": "🏖️"},
    ("sand", "fire"): {"name": "Glass", "emoji": "🔮"},
    ("metal", "fire"): {"name": "Blade", "emoji": "🔪"},
    ("ocean", "earth"): {"name": "Island", "emoji": "🏝️"},
    ("ocean", "fire"): {"name": "Fog", "emoji": "🌫️"},
    ("mountain", "mountain"): {"name": "Mountain Range", "emoji": "🏔️"},
    ("ash", "earth"): {"name": "Soil", "emoji": "🌾"},
    ("rain", "water"): {"name": "Flood", "emoji": "🌊"},
    ("rain", "wind"): {"name": "Storm", "emoji": "⛈️"},
    ("cloud", "cloud"): {"name": "Sky", "emoji": "☁️"},
    ("cloud", "earth"): {"name": "Fog", "emoji": "🌫️"},
    ("fire", "fire"): {"name": "Flame", "emoji": "🔥"},
    ("water", "water"): {"name": "Puddle", "emoji": "💧"},
    ("earth", "earth"): {"name": "Soil", "emoji": "🌾"},
    ("wind", "wind"): {"name": "Tornado", "emoji": "🌪️"},
}

def find_static_recipe(first: str, second: str) -> Optional[dict]:
    key1 = normalize(first)
    key2 = normalize(second)
    for (a, b), result in STATIC_RECIPES.items():
        if (key1 == a and key2 == b) or (key1 == b and key2 == a):
            return {**result, "id": normalize(result["name"])}
    return None

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

    for attempt in range(3):
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
                    timeout=30.0,
                )

            data = resp.json()

            if "error" in data:
                if attempt < 2:
                    continue
                raise Exception(f"OpenRouter error: {data['error']}")

            content = data["choices"][0]["message"]["content"]
            if not content or not isinstance(content, str):
                if attempt < 2:
                    continue
                static_result = find_static_recipe(req.first, req.second)
                if static_result:
                    return static_result
                raise Exception("AI returned empty response")

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

            return {"name": name, "emoji": emoji, "id": normalize(name)}

        except (json.JSONDecodeError, KeyError):
            if attempt < 2:
                continue
            static_result = find_static_recipe(req.first, req.second)
            if static_result:
                return static_result
            raise HTTPException(status_code=500, detail="Could not generate a result")
        except HTTPException:
            raise
        except Exception as e:
            if attempt < 2:
                continue
            static_result = find_static_recipe(req.first, req.second)
            if static_result:
                return static_result
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
