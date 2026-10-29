import subprocess
import os

ACTIONS = [
    {
        "id": "lock",
        "title": "Lock Screen",
        "description": "Lock the current desktop session",
        "icon": "system-lock-screen-symbolic",
        "command": ["loginctl", "lock-session"],
        "keywords": ["lock", "screen", "zakljucaj", "secur"],
    },
    {
        "id": "suspend",
        "title": "Sleep / Suspend",
        "description": "Put system to low-power sleep mode",
        "icon": "media-playback-pause-symbolic",
        "command": ["systemctl", "suspend"],
        "keywords": ["suspend", "sleep", "spavanje", "pauza"],
    },
    {
        "id": "reboot",
        "title": "Restart Computer",
        "description": "Reboot the operating system",
        "icon": "system-reboot-symbolic",
        "command": ["systemctl", "reboot"],
        "keywords": ["reboot", "restart", "ponovo pokreni", "reset"],
    },
    {
        "id": "poweroff",
        "title": "Power Off",
        "description": "Shutdown the computer completely",
        "icon": "system-shutdown-symbolic",
        "command": ["systemctl", "poweroff"],
        "keywords": ["poweroff", "shutdown", "iskljuci", "gašenje", "off"],
    },
    {
        "id": "logout",
        "title": "Log Out",
        "description": "End current user session",
        "icon": "system-log-out-symbolic",
        "command": ["loginctl", "terminate-user", os.environ.get("USER", "")],
        "keywords": ["logout", "log out", "odjava", "odjavi se"],
    },
]

def _word_prefix_match(query: str, text: str) -> bool:
    """True when any word in *text* starts with *query*."""
    for word in text.replace("-", " ").replace("_", " ").split():
        if word.startswith(query):
            return True
    return False


def get_matching_actions(query: str):
    q = query.strip().lower()
    if len(q) < 2:
        return []

    matches = []
    for act in ACTIONS:
        title = act["title"].lower()
        score = 0

        if title == q:
            score += 200
        elif _word_prefix_match(q, title):
            score += 60

        for kw in act["keywords"]:
            if _word_prefix_match(q, kw):
                score += 30
                break

        # Whole command typed inside a longer sentence: "please reboot now"
        for kw in act["keywords"]:
            if len(kw) >= 4 and kw in q:
                score += 20
                break

        if score > 0:
            matches.append((score, act))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matches]

def execute_action(action: dict):
    cmd = action.get("command")
    if cmd and cmd[0]:
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Error executing action {action['id']}: {e}")
