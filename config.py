"""
Configuration for the Hybrid LLM System Agent.
Modify API keys and model settings here.
"""

import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)  # Take environment variables from .env.

# ─── Local Model (Ollama) ────────────────────────────────────────────
LOCAL_MODEL = "ollama/driaforall/tiny-agent-a:0.5b"
LOCAL_API_BASE = "http://localhost:11434"
LOCAL_TIMEOUT = 15  # seconds — fallback to cloud if exceeded

# ─── Spotify API (For Auto-Play) ─────────────────────────────────────
# Need these to convert song names to Spotify URIs.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# ─── Routing Keywords ────────────────────────────────────────────────
# Queries containing these keywords will be routed locally.
LOCAL_KEYWORDS = [
    "open", "close", "launch", "kill", "play", "pause",
    "next", "previous", "skip", "stop", "resume", "volume",
    "spotify", "music", "media", "search", "find",
    "explain", "write a script", "bash script", "complex",
    "summarize", "analyze", "debug", "refactor",
]
