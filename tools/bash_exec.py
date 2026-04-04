"""
Bash Execution — run arbitrary shell commands with human-in-the-loop safety.

SAFETY: Every command is printed in red/bold and requires explicit user
approval (y/N) before execution. This is enforced at the tool level and
cannot be bypassed by the LLM.
"""

import subprocess
import json

from rich.console import Console
from rich.panel import Panel

console = Console()


def run_bash(command: str) -> str:
    """
    Execute a bash command AFTER getting explicit human approval.
    The command is displayed in a highlighted panel and the user
    must type 'y' to approve execution.
    """
    # ─── Human-in-the-loop gate ──────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold white]{command}[/bold white]",
        title="[bold red]⚠  BASH COMMAND APPROVAL REQUIRED[/bold red]",
        border_style="red",
        subtitle="[dim]Type 'y' to approve, anything else to deny[/dim]",
    ))

    try:
        approval = console.input("[bold yellow]>>> Approve? (y/N): [/bold yellow]").strip().lower()
    except (EOFError, KeyboardInterrupt):
        approval = "n"

    if approval != "y":
        return json.dumps({
            "success": False,
            "error": "Command rejected by user.",
        })

    # ─── Execute the approved command ────────────────────────────
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout.strip()[-2000:] if result.stdout else "",
            "stderr": result.stderr.strip()[-2000:] if result.stderr else "",
        }

        if result.returncode == 0:
            console.print("[bold green]✓ Command executed successfully.[/bold green]")
        else:
            console.print(f"[bold red]✗ Command failed (exit {result.returncode}).[/bold red]")

        return json.dumps(output)

    except subprocess.TimeoutExpired:
        return json.dumps({
            "success": False,
            "error": "Command timed out after 60 seconds.",
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
