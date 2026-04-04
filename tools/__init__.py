"""
Tools package — each module exposes functions the LLM can call.
Add new tool modules here and register them in the TOOL_REGISTRY.
"""

from tools.app_control import open_app, close_app
from tools.media_control import media_play, media_pause, media_next, media_previous, media_stop
from tools.web_search import web_search
from tools.bash_exec import run_bash

# ─── Master Tool Registry ────────────────────────────────────────────
# Maps function‑call names to their Python callables.
TOOL_REGISTRY: dict = {
    "open_app": open_app,
    "close_app": close_app,
    "media_play": media_play,
    "media_pause": media_pause,
    "media_next": media_next,
    "media_previous": media_previous,
    "media_stop": media_stop,
    "web_search": web_search,
    "run_bash": run_bash,
}

# ─── OpenAI‑style tool definitions for function calling ──────────────
TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open/launch an application on the Linux desktop by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name or command of the application to open (e.g. 'firefox', 'nautilus', 'code').",
                    }
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Close/kill a running application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the process to kill (e.g. 'firefox', 'spotify').",
                    }
                },
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_play",
            "description": "Play media or a specific track/playlist on Spotify via playerctl.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional: a Spotify URI or search term. Leave empty to resume playback.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_pause",
            "description": "Pause the currently playing media.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_next",
            "description": "Skip to the next track.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_previous",
            "description": "Go back to the previous track.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_stop",
            "description": "Stop media playback entirely.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Open a Google search in the default browser for the given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 5).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a bash command on the local system. Requires human approval before running.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute.",
                    }
                },
                "required": ["command"],
            },
        },
    },
]
