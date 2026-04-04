"""
App Control — open and close Linux desktop applications.
Uses native Linux commands: nohup, pgrep, pkill.
"""

import subprocess
import shutil
import json
import os
import re
import shlex


def open_app(app_name: str) -> str:
    """Launch an application by name. Searches PATH and .desktop files."""
    app_lower = app_name.lower().strip()
    
    # 1. First, check if it's already in PATH directly
    binary = shutil.which(app_lower)
    cmd_list = [binary] if binary else None
    
    # 2. If not found in PATH, search .desktop files
    if not cmd_list:
        search_dirs = [
            os.path.expanduser("~/.local/share/applications"),
            "/usr/share/applications",
            "/var/lib/flatpak/exports/share/applications",
            "/var/lib/flatpak/exports/bin"
        ]
        exec_cmd = None
        for d in search_dirs:
            if exec_cmd or not os.path.exists(d):
                continue
            for root, _, files in os.walk(d):
                if exec_cmd: break
                for file in files:
                    if not file.endswith(".desktop"):
                        continue
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            lines = f.readlines()
                    except Exception:
                        continue
                        
                    current_exec = None
                    matched_name = False
                    
                    # Also check if the filename loosely matches (web apps often have messy names but recognizable parts)
                    if app_lower in file.lower().replace(".desktop", ""):
                        matched_name = True
                        
                    for line in lines:
                        line = line.strip()
                        if line.startswith("Name="):
                            if app_lower in line.split("=", 1)[1].lower():
                                matched_name = True
                        elif line.startswith("Exec="):
                            if not current_exec:
                                # Remove % modifiers (e.g. %U, %u, %F, %f)
                                cmd = line.split("=", 1)[1]
                                cmd = re.sub(r'%[a-zA-Z]', '', cmd).strip()
                                current_exec = cmd
                                
                    if matched_name and current_exec:
                        exec_cmd = current_exec
                        break
        
        if exec_cmd:
            cmd_list = shlex.split(exec_cmd)
            
    if not cmd_list:
        return json.dumps({
            "success": False,
            "error": f"Application '{app_name}' not found locally or in .desktop entries.",
        })

    try:
        subprocess.Popen(
            ["nohup"] + cmd_list,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return json.dumps({
            "success": True,
            "message": f"Launched '{app_name}' successfully.",
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def close_app(app_name: str) -> str:
    """Kill all processes matching `app_name` using pkill."""
    # First check if the process is running
    check = subprocess.run(
        ["pgrep", "-x", app_name],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        # Retry with a broader match (-f flag matches full command line)
        check = subprocess.run(
            ["pgrep", "-f", app_name],
            capture_output=True, text=True,
        )
        if check.returncode != 0:
            return json.dumps({
                "success": False,
                "error": f"No running process found for '{app_name}'.",
            })

    try:
        subprocess.run(["pkill", "-f", app_name], check=True)
        return json.dumps({
            "success": True,
            "message": f"Killed '{app_name}' successfully.",
        })
    except subprocess.CalledProcessError as e:
        return json.dumps({"success": False, "error": str(e)})
