# Infinite Craft Backend

AI-powered element combination backend using OpenRouter.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

## Run

```bash
python main.py
```

Server runs on `http://localhost:8000`

## API

### POST /api/combine
```json
{
  "first": "Water",
  "second": "Fire"
}
```

Returns:
```json
{
  "name": "Steam",
  "emoji": "♨️",
  "id": "steam"
}
```

### GET /api/health
Returns `{"status": "ok"}`
