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
    return re.sub(r'[^\w\s]', '', name.lower().strip().replace('the ', '').replace('a ', '').replace('an ', ''))

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
                        {"role": "user", "content": f"Combine: {req.first} + {req.second}. Return only JSON."},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 100,
                },
                timeout=30.0,
            )

        data = resp.json()

        if "error" in data:
            raise Exception(f"OpenRouter error: {data['error']}")

        content = data["choices"][0]["message"]["content"]

        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(content)

        name = result.get("name", "Unknown")
        emoji = result.get("emoji", "🔹")

        if len(emoji) > 4:
            emoji = get_emoji(name)

        return {"name": name, "emoji": emoji, "id": normalize(name)}

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
