"""
Web Search — opens Google search in the default browser.
"""

import json
import subprocess
import urllib.parse


def web_search(query: str, **_kwargs) -> str:
    """
    Open a Google search in the default browser for the given query.
    """
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"

        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return json.dumps({
            "success": True,
            "message": f"Opened Google search for '{query}'.",
        })

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
