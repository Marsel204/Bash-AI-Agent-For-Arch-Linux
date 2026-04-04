"""
Media Control — manage Spotify / any MPRIS‑compatible player via playerctl.
Requires `playerctl` to be installed:  sudo pacman -S playerctl
"""

import subprocess
import shutil
import json


def _run_playerctl(*args: str) -> tuple[bool, str]:
    """Run a playerctl command and return (success, output)."""
    if shutil.which("playerctl") is None:
        return False, "playerctl is not installed. Install with: sudo pacman -S playerctl"

    try:
        result = subprocess.run(
            ["playerctl", *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "No players found" in stderr:
                return False, "No active media players found. Is Spotify running?"
            return False, stderr or "Unknown playerctl error."
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "playerctl command timed out."
    except Exception as e:
        return False, str(e)


def media_play(query: str = "") -> str:
    """
    Resume playback or open a Spotify URI.
    If `query` is a spotify URI (spotify:track:..., spotify:playlist:...),
    it will be opened directly. Otherwise, plain play/resume.
    """
    if query and query.startswith("spotify:"):
        # Open a specific Spotify URI
        ok, msg = _run_playerctl("--player=spotify", "open", query)
    elif query:
        # 1. Try to get exact track URI via Spotify API
        try:
            import urllib.request
            import urllib.parse
            import base64
            import sys
            import os
            
            # Dynamically import config
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
            
            if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
                # Fast auth token call with strict 3-second timeout to prevent hangs
                auth_str = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
                auth_req = urllib.request.Request(
                    "https://accounts.spotify.com/api/token", 
                    data=b"grant_type=client_credentials",
                    headers={"Authorization": f"Basic {auth_str}", "Content-Type": "application/x-www-form-urlencoded"}
                )
                with urllib.request.urlopen(auth_req, timeout=3) as res:
                    token = json.loads(res.read())["access_token"]
                
                # Fast search call with strict 3-second timeout
                q_enc = urllib.parse.quote(query)
                search_req = urllib.request.Request(
                    f"https://api.spotify.com/v1/search?q={q_enc}&limit=1&type=track",
                    headers={"Authorization": f"Bearer {token}"}
                )
                with urllib.request.urlopen(search_req, timeout=3) as res:
                    data = json.loads(res.read())
                    if data.get("tracks", {}).get("items"):
                        track = data["tracks"]["items"][0]
                        track_uri = track["uri"]
                        
                        # Attempt to play via MPRIS first (instantly switches tracks if already playing)
                        ok, _ = _run_playerctl("--player=spotify", "open", track_uri)
                        
                        if not ok:
                            # If playerctl fails (Spotify is closed), use native command to cold-start and force play
                            subprocess.Popen(
                                ["spotify", f"--uri={track_uri}"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL, 
                                start_new_session=True
                            )
                        
                        return json.dumps({
                            "success": True, 
                            "message": f"Playing '{track['name']}' by {track['artists'][0]['name']} on Spotify."
                        })
        except Exception:
            # If the API times out or fails (e.g., bad keys, network offline), silently fall back
            pass
            
        # 2. Fallback: For non-URI queries where API fails, open spotify web search
        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            search_uri = f"https://open.spotify.com/search/{encoded}"
            subprocess.Popen(
                ["xdg-open", search_uri],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return json.dumps({
                "success": True,
                "message": f"Opened Spotify search for '{query}'. (Auto-play via API failed.)",
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    else:
        ok, msg = _run_playerctl("play")
        if ok:
            return json.dumps({"success": True, "message": "Playback resumed."})
        return json.dumps({"success": False, "error": msg})

    if ok:
        return json.dumps({"success": True, "message": msg or "Playing."})
    return json.dumps({"success": False, "error": msg})


def media_pause() -> str:
    """Pause the current player."""
    ok, msg = _run_playerctl("pause")
    if ok:
        return json.dumps({"success": True, "message": "Playback paused."})
    return json.dumps({"success": False, "error": msg})


def media_next() -> str:
    """Skip to next track."""
    ok, msg = _run_playerctl("next")
    if ok:
        return json.dumps({"success": True, "message": "Skipped to next track."})
    return json.dumps({"success": False, "error": msg})


def media_previous() -> str:
    """Go back to the previous track."""
    ok, msg = _run_playerctl("previous")
    if ok:
        return json.dumps({"success": True, "message": "Went to previous track."})
    return json.dumps({"success": False, "error": msg})


def media_stop() -> str:
    """Stop playback entirely."""
    ok, msg = _run_playerctl("stop")
    if ok:
        return json.dumps({"success": True, "message": "Playback stopped."})
    return json.dumps({"success": False, "error": msg})
