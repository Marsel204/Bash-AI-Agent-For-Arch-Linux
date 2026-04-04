# 🤖 Arch Linux AI System Agent

A local, AI-powered system agent for Arch Linux using a **Hybrid LLM Gateway Architecture**. Routes queries between a lightweight local model (Ollama) 

## Architecture

```
User Prompt
    │
    ▼
┌──────────────┐
│  Router      │──── keyword match ───┐
│  (rule-based)│                      │
└──────┬───────┘                      │
       │                              │
       ▼                              ▼
┌──────────────┐            ┌──────────────┐
│  🏠 LOCAL     │            │  ☁️  CLOUD    │
│  Ollama       │◄─fallback─│  Groq/Gemini │
│  tiny-agent-a:0.5b│  (timeout) │  llama3-70b  │
└──────┬───────┘            └──────┬───────┘
       │                           │
       └─────────┬─────────────────┘
                 ▼
        ┌────────────────┐
        │  Tool Executor │
        │  ┌────────────┐│
        │  │ App Control ││
        │  │ Media Ctrl  ││
        │  │ Web Search  ││
        │  │ Bash Exec   ││
        │  └────────────┘│
        └────────────────┘
```

**Routing Logic:**
- **Local** → simple tasks: open/close apps, media control
- **Cloud** → complex tasks: web search, scripting, analysis
- **Fallback** → if local model times out (5s), automatically routes to cloud

---

## Prerequisites

### System Packages

Install required system packages via `pacman`:

```bash
sudo pacman -S python playerctl
```

| Package | Purpose |
|---------|---------|
| `python` | Python 3.x runtime |
| `playerctl` | MPRIS media player control (Spotify, etc.) |

### Ollama (Local LLM)

Install and start Ollama for the local model route:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the lightweight model
ollama pull driaforall/tiny-agent-a:0.5b

# Verify Ollama is running
ollama list
```

> **Note:** Ollama runs as a systemd service. If it's not running:
> ```bash
> systemctl start ollama
> ```


### Spotify API (Smart Auto-Play)

To allow the `media_play` tool to instantly search atask complexitnd auto-play specific tracks without opening browser tabs, you must provide Spotify Developer credentials:

1. Sign in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new App to get keys.
3. Export them in your environment:
   ```bash
   export SPOTIFY_CLIENT_ID="your_client_id"
   export SPOTIFY_CLIENT_SECRET="your_client_secret"
   ```
*(If the API fails or keys aren't provided, the agent will safely fall back to opening a browser search.)*

---

## Installation

```bash
# Clone or navigate to the project
cd ~/Work/Agent

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## Usage

### Start the Agent

```bash
# Make sure the venv is activated
source .venv/bin/activate

# Run the agent
python agent.py

# Or launch with the interactive Ollama model selector
python agent.py --select
```

You'll see an interactive prompt:

```
╭──────────────────────────────────────────────╮
│     🤖  Arch Linux AI System Agent           │
│  Local: ollama/driaforall/tiny-agent-... | Cloud: ... │
│  Type 'quit' or 'exit' to leave.             │
╰──────────────────────────────────────────────╯

You ▸ _
```

### Example Prompts

| Prompt | Route | Tool Used |
|--------|-------|-----------|
| `Open Firefox` | 🏠 Local | `open_app` |
| `Close Spotify` | 🏠 Local | `close_app` |
| `Play some jazz` | 🏠 Local | `media_play` |
| `Pause the music` | 🏠 Local | `media_pause` |
| `Search the web for Arch Linux tips` | ☁️ Cloud | `web_search` |
| `List all large files in my home directory` | ☁️ Cloud | `run_bash` |

> **🆕 PWA & Flatpak Support:** The `open_app` tool isn't limited to raw binaries — it securely searches your `.desktop` applications (in `~/.local/share/applications` and `/usr/share/applications`), making it perfectly capable of fully parsing and opening Chrome/Brave Progressive Web Apps (PWAs) and Flatpak shortcuts!

### Meta Commands

| Command | Description |
|---------|-------------|
| `/route` | Cycle routing mode: AUTO → LOCAL → CLOUD → AUTO |
| `/clear` | Clear conversation history |
| `/help` | Show help message |
| `quit` / `exit` | Exit the agent |

### Bash Command Safety

When the agent wants to run a bash command, it **always** asks for approval first:

```
╭─ ⚠  BASH COMMAND APPROVAL REQUIRED ─────────╮
│  ls -la ~/Documents                          │
│         Type 'y' to approve, else deny       │
╰──────────────────────────────────────────────╯
>>> Approve? (y/N): _
```

No command runs without you typing `y`.

---

## Project Structure

```
Agent/
├── agent.py              # Main entry point — interactive REPL
├── config.py             # Model config, API keys, routing keywords
├── router.py             # Hybrid routing logic (local vs cloud)
├── requirements.txt      # Python dependencies
├── README.md
└── tools/
    ├── __init__.py        # Tool registry & OpenAI-style definitions
    ├── app_control.py     # Open/close apps (nohup, pkill)
    ├── media_control.py   # Spotify/MPRIS control (playerctl)
    ├── web_search.py      # DuckDuckGo search
    └── bash_exec.py       # Bash execution with human approval
```

---

## Configuration

All settings live in `config.py`:

```python
# Switch the local model
LOCAL_MODEL = "ollama/driaforall/tiny-agent-a:0.5b"

# Switch the cloud model
CLOUD_MODEL = "groq/llama3-70b-8192"

# Adjust local timeout before cloud fallback
LOCAL_TIMEOUT = 5  # seconds

# Add keywords for routing
LOCAL_KEYWORDS = ["open", "close", "play", ...]
CLOUD_KEYWORDS = ["search", "explain", "script", ...]
```

---

## Adding New Tools

The project is modular — adding a new tool takes 3 steps:

### 1. Create the tool module

```python
# tools/my_tool.py
import json

def my_tool(param: str) -> str:
    """Do something useful."""
    # ... your logic ...
    return json.dumps({"success": True, "message": "Done!"})
```

### 2. Register it in `tools/__init__.py`

```python
from tools.my_tool import my_tool

# Add to TOOL_REGISTRY
TOOL_REGISTRY["my_tool"] = my_tool

# Add to TOOL_DEFINITIONS
TOOL_DEFINITIONS.append({
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Description for the LLM.",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "..."}
            },
            "required": ["param"],
        },
    },
})
```

### 3. Update the system prompt in `agent.py`

Add your tool name and description to the `SYSTEM_PROMPT` string so the LLM knows about it.

---

## Quick Alias Setup

Add this to your `~/.bashrc` or `~/.zshrc` for one-command launch:

```bash
alias agent='source ~/Work/Agent/.venv/bin/activate && python ~/Work/Agent/agent.py'
```

Then just run:

```bash
agent
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ollama: command not found` | Install Ollama: `curl -fsSL https://ollama.com/install.sh \| sh` |
| `No players found` | Start Spotify or another MPRIS player first |
| `playerctl: command not found` | `sudo pacman -S playerctl` |
| Local model too slow | Increase `LOCAL_TIMEOUT` in `config.py` or use `/route` to force cloud |
| `ModuleNotFoundError` | Make sure venv is activated: `source .venv/bin/activate` |

---

## License

MIT — do whatever you want with it.
