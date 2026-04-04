"""
Configuration for the Hybrid LLM System Agent.
Modify API keys and model settings here.
"""

import os

# ─── Local Model (Ollama) ────────────────────────────────────────────
LOCAL_MODEL = "ollama/driaforall/tiny-agent-a:0.5b"
LOCAL_API_BASE = "http://localhost:11434"
LOCAL_TIMEOUT = 15  # seconds — fallback to cloud if exceeded

# ─── Spotify API (For Auto-Play) ─────────────────────────────────────
# Need these to convert song names to Spotify URIs.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "0b07d3a693c24b73a0582a9255bc1d8d")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "33b06769ad744b48a816184a5712d5c5")

# ─── Routing Keywords ────────────────────────────────────────────────
# Queries containing these keywords will be routed locally.
LOCAL_KEYWORDS = [
    "open", "close", "launch", "kill", "play", "pause",
    "next", "previous", "skip", "stop", "resume", "volume",
    "spotify", "music", "media", "search", "find",
    "explain", "write a script", "bash script", "complex",
    "summarize", "analyze", "debug", "refactor",
]