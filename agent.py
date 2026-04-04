#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║       Arch Linux AI System Agent — Hybrid LLM Gateway              ║
║                                                                    ║
║  Routes queries between a local Ollama model and a cloud API.      ║
║  Supports tool calling for app control, media, web search, bash.   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import re
import sys
import os

import litellm
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

import config
from router import classify_route, get_model_for_route, Route
from tools import TOOL_REGISTRY, TOOL_DEFINITIONS

# ─── Setup ────────────────────────────────────────────────────────────
console = Console()

# Suppress litellm's verbose logging
litellm.suppress_debug_info = True
litellm.set_verbose = False

# Set API keys for litellm
# LiteLLM will automatically read OPENROUTER_API_KEY from os.environ, which we set in config.py
# System prompt — optimized for small local models to output structured JSON
SYSTEM_PROMPT = """You are a system agent. You control a Linux computer using tools.
Respond with ONLY a JSON object when using a tool. No other text.

Format: {"tool": "TOOL_NAME", "args": {"param": "value"}}

Tools:
- open_app: Launch a local desktop application using its command name. Args: app_name
- close_app: Close an app. Args: app_name
- media_play: Play music on Spotify. Args: query (optional)
- media_pause: Pause music. No args.
- media_next: Next song. No args.
- media_previous: Previous song. No args.
- media_stop: Stop music. No args.
- web_search: Search the web / internet. Args: query
- run_bash: Run shell command. Args: command

Examples:
User: Open chromium
Assistant: {"tool": "open_app", "args": {"app_name": "chromium"}}

User: Search the web for alan walker
Assistant: {"tool": "web_search", "args": {"query": "alan walker"}}

User: Look up arch linux tips
Assistant: {"tool": "web_search", "args": {"query": "arch linux tips"}}

User: play anytime anywhere by millet
Assistant: {"tool": "media_play", "args": {"query": "anytime anywhere millet"}}

User: Play some jazz
Assistant: {"tool": "media_play", "args": {"query": "jazz"}}

User: List files in home
Assistant: {"tool": "run_bash", "args": {"command": "ls ~"}}

User: What time is it?
Assistant: {"tool": "run_bash", "args": {"command": "date"}}

If no tool is needed, reply with plain text. NEVER add text before or after the JSON.
"""

# Conversation history
messages: list[dict] = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


# ─── LLM Call ──────────────────────────────────────────────────────────
def call_llm(model: str, msgs: list[dict], route: str) -> dict:
    """Call the LLM local endpoint."""
    try:
        return litellm.completion(
            model=model,
            messages=msgs,
            timeout=config.LOCAL_TIMEOUT,
            temperature=0.1,
        )
    except Exception as e:
        console.print(f"[red]⚡ Local model failed: {e}[/red]")
        raise



# ─── Parse Tool Calls from Plain Text ────────────────────────────────
def parse_tool_from_text(text: str) -> dict | None:
    """
    Attempt to extract a tool call from the LLM's plain text response.
    Small local models often return raw JSON instead of using the
    structured tool_calls API. This function handles multiple formats:

      Format 1: {"tool": "name", "args": {...}}
      Format 2: {"type": "function", "name": "name", "parameters": {...}}
      Format 3: {"name": "name", "parameters": {...}}
    """
    if not text:
        return None

    # Clean up the text — remove markdown formatting
    clean = text.strip()
    # Remove code fences if present
    clean = re.sub(r'^```(?:json)?\s*', '', clean)
    clean = re.sub(r'\s*```$', '', clean)
    clean = clean.strip()

    # Strategy 1: Try the entire cleaned text as JSON
    candidates = []
    if clean.startswith("{"):
        candidates.append(clean)

    # Strategy 2: Extract all JSON-like objects with regex
    # This handles cases where the model adds text around the JSON
    for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL):
        candidates.append(match.group())

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(data, dict):
            continue

        # Format 1: {"tool": "name", "args": {...}}
        if "tool" in data and isinstance(data["tool"], str):
            tool_name = data["tool"]
            if tool_name in TOOL_REGISTRY:
                return {
                    "name": tool_name,
                    "args": data.get("args", data.get("parameters", {})) or {},
                }

        # Format 2: {"type": "function", "name": "...", "parameters": {...}}
        if data.get("type") == "function" and isinstance(data.get("name"), str):
            tool_name = data["name"]
            if tool_name in TOOL_REGISTRY:
                return {
                    "name": tool_name,
                    "args": data.get("parameters", data.get("args", {})) or {},
                }

        # Format 3: {"name": "...", "parameters": {...}}
        if isinstance(data.get("name"), str) and data["name"] in TOOL_REGISTRY:
            return {
                "name": data["name"],
                "args": data.get("parameters", data.get("args", {})) or {},
            }

    return None


# ─── Tool Execution ──────────────────────────────────────────────────
def execute_tool_call(tool_call) -> str:
    """Execute a tool from a structured API tool_call object."""
    func_name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        args = {}
    return _run_tool(func_name, args)


def execute_parsed_tool(parsed: dict) -> str:
    """Execute a tool from a text-parsed dict {"name": ..., "args": ...}."""
    return _run_tool(parsed["name"], parsed.get("args", {}))


def _run_tool(func_name: str, args: dict) -> str:
    """Common tool execution logic."""
    func = TOOL_REGISTRY.get(func_name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {func_name}"})

    console.print(f"[cyan]🔧 Calling tool:[/cyan] [bold]{func_name}[/bold]({args})")

    try:
        result = func(**args)
        return result
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {func_name}: {e}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {e}"})


def show_tool_result(result: str):
    """Print a colored preview of the tool result."""
    try:
        parsed = json.loads(result)
        success = parsed.get("success", None)
        if success is True:
            console.print(f"[green]   ✓ {parsed.get('message', 'OK')}[/green]")
        elif success is False:
            console.print(f"[red]   ✗ {parsed.get('error', 'Failed')}[/red]")
        else:
            # For web search results etc.
            if "results" in parsed:
                for r in parsed["results"][:3]:
                    console.print(f"[dim]   • {r.get('title', '')}: {r.get('url', '')}[/dim]")
    except json.JSONDecodeError:
        pass


# ─── Process a Single Turn ───────────────────────────────────────────
def process_turn(user_input: str, route_override: str | None = None):
    """
    Full processing loop for one user message:
      1. Route the query
      2. Call the LLM
      3. Handle tool calls (structured API or text-parsed JSON)
      4. Print the final text response
    """
    # Determine routing
    route = route_override if route_override else classify_route(user_input)
    model = get_model_for_route(route)
    console.print(f"[dim]Route: 🏠 LOCAL → {model}[/dim]")

    # Add user message to history
    messages.append({"role": "user", "content": user_input})

    # Call the LLM (with fallback)
    try:
        response = call_llm(model, messages, route)
    except Exception as e:
        console.print(f"[bold red]✗ LLM Error:[/bold red] {e}")
        console.print("[dim]Check your API key and network connection.[/dim]")
        messages.pop()  # Remove the failed user message
        return

    assistant_msg = response.choices[0].message

    # ─── Tool call loop ───────────────────────────────────────────
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # ── Case A: Structured tool calls (cloud models) ──────────
        if assistant_msg.tool_calls:
            messages.append(assistant_msg.model_dump())

            for tc in assistant_msg.tool_calls:
                result = execute_tool_call(tc)
                show_tool_result(result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # Call the LLM again with the tool results
            try:
                response = call_llm(model, messages, route)
            except Exception as e:
                console.print(f"[bold red]✗ LLM Error on follow-up:[/bold red] {e}")
                break
            assistant_msg = response.choices[0].message
            continue

        # ── Case B: Text-embedded tool call (local models) ────────
        content = assistant_msg.content or ""
        parsed_tool = parse_tool_from_text(content)

        if parsed_tool:
            result = execute_parsed_tool(parsed_tool)
            show_tool_result(result)

            # Build a simple summary from the tool result
            try:
                result_data = json.loads(result)
                if result_data.get("success"):
                    summary = result_data.get("message", "Done.")
                else:
                    summary = f"Error: {result_data.get('error', 'Unknown error.')}"
            except json.JSONDecodeError:
                summary = result

            # Add to history and show summary — do NOT call the model again
            # (the 1B model will just repeat the same tool call in a loop)
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "assistant", "content": summary})

            console.print()
            console.print(Panel(
                summary,
                title="[bold blue]Agent[/bold blue]",
                border_style="blue",
                padding=(1, 2),
            ))
            return  # Done — tool executed once, result shown

        # ── Case C: No tool call — just a text response ──────────
        break

    # ─── Final text response from the LLM ────────────────────────
    reply = assistant_msg.content or ""

    # Don't display the reply if it's just a raw tool JSON (already handled)
    if reply and not parse_tool_from_text(reply):
        messages.append({"role": "assistant", "content": reply})
        console.print()
        console.print(Panel(
            Markdown(reply),
            title="[bold blue]Agent[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        ))
    elif not reply:
        messages.append({"role": "assistant", "content": ""})


# ─── Interactive REPL ────────────────────────────────────────────────
def print_banner():
    banner = Table(show_header=False, box=None, padding=(0, 1))
    banner.add_column(style="bold cyan", justify="center")
    banner.add_row("🤖  Arch Linux AI System Agent")
    
    # Clean up the model name for display
    display_model = config.LOCAL_MODEL.split('/')[-1] if config.LOCAL_MODEL.startswith("ollama/") else config.LOCAL_MODEL
    banner.add_row(f"Local Model: {display_model}")
    banner.add_row("[dim]Type 'quit' or 'exit' to leave.[/dim]")

    console.print()
    console.print(Panel(banner, border_style="bright_cyan", padding=(1, 2)))
    console.print()


def main():
    import sys
    if "--select" in sys.argv:
        try:
            import urllib.request
            import json
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as response:
                models = json.loads(response.read()).get("models", [])
            
            if not models:
                console.print("[red]No models found in Ollama![/red]")
            else:
                console.print("\n[bold cyan]Available Ollama Models:[/bold cyan]")
                for idx, m in enumerate(models):
                    # Show size or details if needed? Name is enough for now.
                    console.print(f"  [green]{idx + 1}[/green]. {m['name']}")
                
                default_display = config.LOCAL_MODEL.split('/')[-1] if config.LOCAL_MODEL.startswith("ollama/") else config.LOCAL_MODEL
                while True:
                    choice = console.input(f"\n[cyan]Select a model (1-{len(models)}) or press Enter to keep default [{default_display}]: [/cyan]").strip()
                    if not choice:
                        console.print(f"[dim]Keeping default: {default_display}[/dim]\n")
                        break
                    if choice.isdigit() and 1 <= int(choice) <= len(models):
                        selected_name = models[int(choice) - 1]["name"]
                        config.LOCAL_MODEL = f"ollama/{selected_name}"
                        console.print(f"[bold green]✓ Switched to {selected_name}[/bold green]\n")
                        break
                    console.print(f"[red]Invalid choice. Please enter a number between 1 and {len(models)}.[/red]")
        except Exception as e:
            console.print(f"[red]Failed to fetch Ollama models: {e}[/red]\n")
            
    print_banner()

    manual_route = None  # None = auto, or "local" / "cloud"

    while True:
        try:
            prompt = console.input("[bold green]You ▸ [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not prompt:
            continue

        # ─── Meta commands ────────────────────────────────────────
        if prompt.lower() in ("quit", "exit", "/quit", "/exit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if prompt.lower() == "/route":
            if manual_route is None:
                manual_route = "local"
                console.print("[yellow]Manual routing: LOCAL[/yellow]")
            elif manual_route == "local":
                manual_route = "cloud"
                console.print("[yellow]Manual routing: CLOUD[/yellow]")
            else:
                manual_route = None
                console.print("[yellow]Routing: AUTO (keyword-based)[/yellow]")
            continue

        if prompt.lower() == "/clear":
            messages.clear()
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
            console.print("[yellow]Conversation history cleared.[/yellow]")
            continue

        if prompt.lower() == "/help":
            console.print(Markdown("""
**Commands:**
- `/route` — Cycle routing: AUTO → LOCAL → CLOUD → AUTO
- `/clear` — Clear conversation history
- `/help`  — Show this help
- `quit`   — Exit the agent

**Example prompts:**
- "Open Firefox"
- "Play some jazz on Spotify"
- "Search the web for Arch Linux tips"
- "List all files in my home directory"
"""))
            continue

        # ─── Override route if manual ─────────────────────────────
        if manual_route:
            process_turn(prompt, route_override=manual_route)
        else:
            process_turn(prompt)


if __name__ == "__main__":
    main()
