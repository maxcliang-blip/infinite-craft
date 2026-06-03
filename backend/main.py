import json
import os
import re
import sqlite3
import threading
from typing import Optional
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

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = "http://" + OLLAMA_URL
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
DB_PATH = os.path.join(os.path.dirname(__file__), "recipes.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_recipes (
            cache_key TEXT PRIMARY KEY,
            first TEXT NOT NULL,
            second TEXT NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

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
    "slime": "🟢", "human": "🧑", "life": "🧬", "energy": "⚡",
    "time": "⏰", "home": "🏠", "blade": "🔪", "sword": "⚔️",
    "wrought iron": "⛓️", "iron": "⛓️", "steel": "⚙️",
    "aging leaf": "🍂", "leaf": "🍃", "ashes": "🌫️",
    "wrought": "⛓️", "irony": "🎭",
    "wood": "🪵", "coal": "⬛", "diamond": "💎",
    "crystal": "💎", "ruin": "🏚️", "ruins": "🏚️",
    "sword": "⚔️", "shield": "🛡️", "armor": "🛡️",
    "tool": "🔧", "hammer": "🔨", "spear": "🗡️",
    "arrow": "🏹", "bow": "🏹", "machine": "⚙️",
    "robot": "🤖", "android": "🤖", "clock": "⏰",
    "wheel": "☸️", "fossil": "🦴", "bone": "🦴",
    "corpse": "💀", "skeleton": "💀", "ghost": "👻",
    "spirit": "👻", "zombie": "🧟", "vampire": "🧛",
    "dragon": "🐉", "phoenix": "🔥", "unicorn": "🦄",
    "fish": "🐟", "bird": "🐦", "snake": "🐍",
    "insect": "🐛", "spider": "🕷️", "bee": "🐝",
    "wolf": "🐺", "bear": "🐻", "cat": "🐱",
    "dog": "🐕", "horse": "🐴", "cow": "🐮",
    "pig": "🐷", "chicken": "🐔", "frog": "🐸",
    "mushroom": "🍄", "flower": "🌸", "seed": "🌰",
    "fruit": "🍎", "apple": "🍎", "berry": "🫐",
    "bread": "🍞", "cheese": "🧀", "egg": "🥚",
    "milk": "🥛", "tea": "🍵", "coffee": "☕",
    "beer": "🍺", "wine": "🍷", "potion": "🧪",
    "poison": "☠️", "explosion": "💥", "bomb": "💣",
    "electricity": "⚡", "electric": "⚡", "wire": "🔌",
    "battery": "🔋", "light": "💡", "bulb": "💡",
    "mirror": "🪞", "painting": "🖼️", "paint": "🎨",
    "music": "🎵", "song": "🎶", "note": "🎵",
    "book": "📖", "paper": "📄", "pen": "🖊️",
    "key": "🔑", "lock": "🔒", "chest": "📦",
    "treasure": "💰", "gold": "🪙", "silver": "🥈",
    "copper": "🥉", "bronze": "🥉",
    "bridge": "🌉", "tower": "🗼", "castle": "🏰",
    "ship": "🚢", "boat": "⛵", "car": "🚗",
    "train": "🚂", "plane": "✈️", "rocket": "🚀",
    "computer": "💻", "phone": "📱", "screen": "🖥️",
    "internet": "🌐", "network": "🌐", "web": "🕸️",
    "virus": "🦠", "bacteria": "🦠", "cell": "🧫",
    "dna": "🧬", "gene": "🧬", "mutation": "🧬",
    "plague": "☠️", "disease": "🤒", "medicine": "💊",
    "pill": "💊", "heal": "💚", "heart": "❤️",
    "love": "💕", "blood": "🩸", "bone": "🦴",
    "ice": "🧊", "snow": "❄️", "blizzard": "🌨️",
    "frost": "❄️", "cold": "🥶", "freeze": "🧊",
    "puddle": "💧", "lake": "🏞️", "river": "🏞️",
    "waterfall": "💦", "flood": "🌊", "tsunami": "🌊",
    "drought": "☀️", "desert": "🏜️", "dune": "🏜️",
    "oasis": "🏝️", "cave": "🕳️", "crystal": "💎",
    "mine": "⛏️", "ore": "🪨", "gem": "💎",
    "jewel": "💎", "crown": "👑", "ring": "💍",
    "staff": "🪄", "wand": "🪄", "magic": "✨",
    "spell": "✨", "wizard": "🧙", "witch": "🧙‍♀️",
    "demon": "👿", "angel": "👼", "god": "⚡",
    "sky": "☁️", "space": "🌌", "star": "⭐",
    "planet": "🪐", "moon": "🌙", "sun": "☀️",
    "eclipse": "🌑", "comet": "☄️", "meteor": "☄️",
    "gravity": "🪐", "black hole": "🕳️", "void": "🕳️",
    "dream": "💭", "nightmare": "😱", "sleep": "😴",
    "thought": "💭", "idea": "💡", "brain": "🧠",
    "mind": "🧠", "soul": "👻", "consciousness": "🧠",
    "wisdom": "📚", "knowledge": "📚", "science": "🔬",
    "math": "🔢", "physics": "⚛️", "chemistry": "🧪",
    "biology": "🧬", "history": "📜", "ancient": "🏛️",
    "pyramid": "🏛️", "statue": "🗿", "monument": "🗿",
    "flag": "🏳️", "banner": "🏴", "sign": "🪧",
    "road": "🛣️", "path": "🛤️", "trail": "🥾",
    "map": "🗺️", "compass": "🧭", "direction": "🧭",
    "north": "🧭", "south": "🧭", "east": "🧭", "west": "🧭",
    "dawn": "🌅", "dusk": "🌇", "sunrise": "🌅", "sunset": "🌇",
    "night": "🌃", "day": "☀️", "dawn": "🌅",
    "season": "🍂", "spring": "🌸", "summer": "☀️",
    "autumn": "🍂", "fall": "🍂", "winter": "❄️",
    "tornado": "🌪️", "hurricane": "🌀", "storm": "⛈️",
    "lightning": "⚡", "rainbow": "🌈", "aurora": "🌌",
    "dust": "✨", "pollen": "🌼", "spore": "🍄",
    "vine": "🌿", "root": "🌱", "branch": "🌿",
    "grass": "🌿", "hay": "🌾", "straw": "🌾",
    "rope": "🪢", "chain": "⛓️", "link": "🔗",
    "fabric": "🧵", "cloth": "🧶", "thread": "🧵",
    "needle": "🪡", "scissors": "✂️", "knife": "🔪",
    "blunt": "🪨", "sharp": "🔪", "edge": "🗡️",
    "sword": "⚔️", "axe": "🪓", "pickaxe": "⛏️",
    "shovel": "🪏", "rake": "🌾", "hoe": "🌾",
    "plow": "🚜", "tractor": "🚜", "farm": "🚜",
    "barn": "🏚️", "silo": "🏗️", "well": "🕳️",
    "spring": "💧", "source": "💧", "fountain": "⛲",
    "geyser": "♨️", "hot spring": "♨️", "sauna": "🧖",
    "steam": "♨️", "pressure": "🔥", "heat": "🌡️",
    "temperature": "🌡️", "thermometer": "🌡️",
    "radiation": "☢️", "nuclear": "☢️", "atom": "⚛️",
    "molecule": "🔬", "particle": "⚛️", "electron": "⚡",
    "proton": "⚛️", "neutron": "⚛️", "ion": "⚡",
    "plasma": "⚡", "gas": "💨", "liquid": "💧",
    "solid": "🪨", "matter": "📦", "mass": "📦",
    "weight": "⚖️", "scale": "⚖️", "balance": "⚖️",
    "force": "💪", "power": "⚡", "strength": "💪",
    "speed": "💨", "velocity": "💨", "acceleration": "💨",
    "momentum": "💨", "motion": "🏃", "movement": "🏃",
    "run": "🏃", "walk": "🚶", "fly": "🕊️",
    "swim": "🏊", "jump": "🦘", "hop": "🐇",
    "bounce": "🏀", "roll": "🎲", "spin": "🌀",
    "rotate": "🔄", "turn": "🔄", "twist": "🌀",
    "break": "💥", "crack": "💔", "shatter": "💥",
    "destroy": "💥", "create": "✨", "build": "🏗️",
    "construct": "🏗️", "make": "🛠️", "craft": "🛠️",
    "forge": "🔥", "smelt": "🔥", "melt": "🫠",
    "boil": "♨️", "cook": "🍳", "fry": "🍳",
    "bake": "🍰", "roast": "🔥", "grill": "🔥",
    "soup": "🍲", "stew": "🍲", "salad": "🥗",
    "sandwich": "🥪", "pizza": "🍕", "pasta": "🍝",
    "rice": "🍚", "noodle": "🍜", "bowl": "🥣",
    "plate": "🍽️", "fork": "🍴", "spoon": "🥄",
    "cup": "☕", "glass": "🥂", "bottle": "🍾",
    "jar": "🫙", "box": "📦", "bag": "👜",
    "pocket": "👖", "wallet": "👛", "purse": "👛",
    "money": "💰", "coin": "🪙", "bill": "💵",
    "bank": "🏦", "store": "🏪", "shop": "🏪",
    "market": "🏪", "mall": "🏬", "building": "🏢",
    "skyscraper": "🏙️", "city": "🏙️", "town": "🏘️",
    "village": "🏘️", "kingdom": "👑", "empire": "👑",
    "nation": "🏳️", "country": "🌍", "world": "🌍",
    "universe": "🌌", "multiverse": "🌌", "dimension": "🌌",
    "portal": "🌀", "gateway": "🚪", "door": "🚪",
    "window": "🪟", "glass": "🔮", "crystal": "💎",
    "prism": "🔮", "lens": "🔍", "telescope": "🔭",
    "microscope": "🔬", "magnify": "🔍", "search": "🔍",
    "look": "👁️", "see": "👁️", "watch": "⌚",
    "clock": "⏰", "hour": "⏰", "minute": "⏱️",
    "second": "⏱️", "moment": "⚡", "instant": "⚡",
    "forever": "♾️", "eternal": "♾️", "infinity": "♾️",
    "limit": "🔒", "boundary": "🚧", "wall": "🧱",
    "fence": "🏗️", "gate": "🚪", "barrier": "🚧",
    "prison": "⛓️", "jail": "⛓️", "cell": "🔒",
    "free": "🕊️", "freedom": "🕊️", "liberty": "🗽",
    "peace": "☮️", "war": "⚔️", "battle": "⚔️",
    "fight": "🥊", "punch": "👊", "kick": "🦵",
    "slap": "🖐️", "hit": "💥", "strike": "⚡",
    "attack": "⚔️", "defend": "🛡️", "protect": "🛡️",
    "guard": "🛡️", "sentinel": "🛡️", "watchman": "👁️",
    "spy": "🕵️", "detective": "🕵️", "investigation": "🔍",
    "clue": "🔍", "evidence": "📋", "proof": "✅",
    "truth": "💯", "lie": "🤥", "secret": "🤫",
    "whisper": "🤫", "shout": "📢", "scream": "😱",
    "yell": "📢", "talk": "🗣️", "speak": "🗣️",
    "voice": "🎤", "sound": "🔊", "noise": "📢",
    "silence": "🔇", "quiet": "🤫", "mute": "🔇",
    "deaf": "🔇", "blind": "👁️‍🗨️", "dark": "🌑",
    "shadow": "🌑", "shade": "🌑", "gloom": "🌑",
    "horror": "😱", "terror": "😱", "fear": "😨",
    "scare": "👻", "spook": "👻", "haunt": "👻",
    "cursed": "🔮", "blessed": "✨", "holy": "✝️",
    "sacred": "✝️", "holy water": "💧", "holy fire": "🔥",
    "holy ground": "⛪", "church": "⛪", "temple": "⛩️",
    "shrine": "⛩️", "altar": "🕯️", "candle": "🕯️",
    "flame": "🔥", "torch": "🔦", "lantern": "🏮",
    "lamp": "💡", "lightbulb": "💡", "flashlight": "🔦",
    "glow": "✨", "shine": "✨", "sparkle": "✨",
    "twinkle": "✨", "flash": "📸", "blink": "👁️",
    "wink": "😉", "smile": "😊", "laugh": "😄",
    "cry": "😢", "sob": "😭", "weep": "😭",
    "joy": "😄", "happiness": "😊", "sadness": "😢",
    "anger": "😠", "rage": "🤬", "fury": "🤬",
    "calm": "😌", "peace": "☮️", "serene": "😌",
    "zen": "🧘", "meditation": "🧘", "yoga": "🧘",
    "pose": "🧘", "stretch": "🤸", "flex": "💪",
    "muscle": "💪", "bicep": "💪", "body": "🦴",
    "flesh": "🥩", "meat": "🥩", "steak": "🥩",
    "raw": "🥩", "cooked": "🍳", "done": "✅",
    "finished": "✅", "complete": "✅", "perfect": "💯",
    "flawless": "💎", "imperfect": "💔", "broken": "💔",
    "fixed": "🔧", "repaired": "🔧", "healed": "💚",
    "healthy": "💚", "sick": "🤒", "ill": "🤒",
    "dead": "💀", "alive": "❤️", "living": "🧬",
    "undead": "🧟", "immortal": "♾️", "mortal": "⏳",
    "death": "💀", "birth": "👶", "life": "🧬",
    "cycle": "🔄", "loop": "🔄", "circle": "⭕",
    "ring": "💍", "band": "💍", "circle": "⭕",
    "sphere": "🔵", "ball": "⚽", "orb": "🔮",
    "marble": "🔵", "pearl": "🫧", "bubble": "🫧",
    "foam": "🫧", "suds": "🫧", "soap": "🧼",
    "clean": "🧼", "dirty": "💩", "filth": "💩",
    "trash": "🗑️", "garbage": "🗑️", "waste": "🗑️",
    "recycle": "♻️", "reuse": "♻️", "reduce": "♻️",
    "eco": "♻️", "green": "🟢", "environment": "🌍",
    "nature": "🌿", "wild": "🐺", "tame": "🐕",
    "pet": "🐾", "paw": "🐾", "claw": "🐾",
    "fang": "🦷", "tooth": "🦷", "teeth": "🦷",
    "bite": "🦷", "chew": "🦷", "eat": "🍽️",
    "consume": "🍽️", "devour": "🍽️", "swallow": "🫦",
    "digest": "🫦", "absorb": "🧽", "soak": "🧽",
    "sponge": "🧽", "cloth": "🧽", "towel": "🧽",
    "dry": "☀️", "wet": "💦", "damp": "💧",
    "humid": "💧", "moist": "💧", "arid": "🏜️",
    "bone": "🦴",
}

def get_emoji(name: str) -> str:
    key = name.lower()
    return EMOJI_MAP.get(key, "🔹")

def is_emoji_valid(emoji: str, name: str) -> bool:
    if not emoji or not isinstance(emoji, str):
        return False
    name_lower = name.lower()
    person_emojis = {"🧑", "👤", "👥", "👦", "👧", "👨", "👩", "🧒", "👴", "👵", "👶", "👱", "🧔", "👲", "👳", "👮", "👷", "💂", "🕵️", "👨‍⚕️", "👩‍⚕️", "👨‍🌾", "👩‍🌾", "👨‍🍳", "👩‍🍳", "👨‍🎓", "👩‍🎓", "👨‍🎤", "👩‍🎤", "👨‍🏫", "👩‍🏫", "👨‍🏭", "👩‍🏭", "👨‍💻", "👩‍💻", "👨‍💼", "👩‍💼", "👨‍🔧", "👩‍🔧", "👨‍🔬", "👩‍🔬", "👨‍🎨", "👩‍🎨", "👨‍🚀", "👩‍🚀", "👨‍🚒", "👩‍🚒", "👨‍✈️", "👩‍✈️", "👨‍⚖️", "👩‍⚖️"}
    if emoji in person_emojis and "human" not in name_lower and "person" not in name_lower and "people" not in name_lower and "man" not in name_lower and "woman" not in name_lower and "child" not in name_lower and "boy" not in name_lower and "girl" not in name_lower and "crowd" not in name_lower:
        return False
    if len(emoji) > 4:
        return False
    return True

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

SYSTEM_PROMPT = """You are a creative item-discovery engine for a crafting game.

When given two elements, invent ONE NEW item that their combination produces.

STRICT RULES:
1. NEVER return either input element as the result
2. NEVER return both elements joined together
3. ALWAYS create something new and different
4. Return ONLY this JSON format: {"name": "ResultName", "emoji": "🔹"}
5. Name must be 1-3 words, Title Case
6. Emoji must be a SINGLE emoji character

THINK about:
- Physical reactions: melting, burning, growing, aging
- Materials: compounds, mixtures, alloys
- Nature: plants, animals, weather, geology
- Human creations: tools, buildings, art, technology
- Abstract ideas: energy, time, emotions

EXAMPLES:
Fire + Water = {"name": "Steam", "emoji": "♨️"}
Earth + Fire = {"name": "Lava", "emoji": "🌋"}
Time + Stone = {"name": "Fossil", "emoji": "🦴"}
Sand + Fire = {"name": "Glass", "emoji": "🔮"}

Output ONLY the JSON. Nothing else."""

def get_cached(cache_key: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT name, emoji FROM ai_recipes WHERE cache_key = ?", (cache_key,)).fetchone()
    conn.close()
    if row:
        return make_response(row["name"], row["emoji"])
    return None

def save_recipe(cache_key: str, first: str, second: str, name: str, emoji: str):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO ai_recipes (cache_key, first, second, name, emoji) VALUES (?, ?, ?, ?, ?)",
        (cache_key, first, second, name, emoji)
    )
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    print(f"Infinite Craft started with Ollama: {OLLAMA_URL}, model: {OLLAMA_MODEL}")

@app.post("/api/combine")
async def combine(req: CombineRequest):
    cache_key = make_cache_key(req.first, req.second)

    if cache_key in STATIC_RECIPES:
        r = STATIC_RECIPES[cache_key]
        return make_response(r["name"], r["emoji"])

    cached = get_cached(cache_key)
    if cached:
        return cached
    for attempt in range(2):
        try:
            async with AsyncClient() as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/chat",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Combine: {req.first} + {req.second}. Return only JSON like {{\"name\": \"Something\", \"emoji\": \"🔹\"}}"},
                        ],
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 80,
                        },
                        "stream": False,
                    },
                    timeout=120.0,
                )

            data = resp.json()
            content = data.get("message", {}).get("content", "")
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
            map_emoji = get_emoji(name)
            if map_emoji != "🔹":
                emoji = map_emoji
            elif not is_emoji_valid(emoji, name):
                emoji = "🔹"

            first_norm = normalize(req.first)
            second_norm = normalize(req.second)
            name_norm = normalize(name)
            if name_norm == first_norm or name_norm == second_norm:
                if attempt < 1:
                    continue
                return make_response("Unknown", "🔹")

            save_recipe(cache_key, req.first, req.second, name, emoji)
            return make_response(name, emoji)

        except (json.JSONDecodeError, KeyError):
            if attempt < 1:
                continue
        except Exception:
            if attempt < 1:
                continue

    return make_response("Unknown", "🔹")

@app.get("/api/health")
async def health():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM ai_recipes").fetchone()[0]
    conn.close()
    return {"status": "ok", "model": OLLAMA_MODEL, "db_recipes": count, "static_recipes": len(STATIC_RECIPES)}

@app.get("/api/recipes")
async def list_recipes():
    conn = get_db()
    rows = conn.execute("SELECT first, second, name, emoji FROM ai_recipes ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
