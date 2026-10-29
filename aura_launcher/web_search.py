import urllib.parse
import webbrowser

PROVIDERS = {
    "g": {"name": "Google", "url": "https://www.google.com/search?q={}", "icon": "web-browser-symbolic"},
    "ddg": {"name": "DuckDuckGo", "url": "https://duckduckgo.com/?q={}", "icon": "web-browser-symbolic"},
    "yt": {"name": "YouTube", "url": "https://www.youtube.com/results?search_query={}", "icon": "video-x-generic-symbolic"},
    "gh": {"name": "GitHub", "url": "https://github.com/search?q={}", "icon": "utilities-terminal-symbolic"},
    "wiki": {"name": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Special:Search?search={}", "icon": "help-about-symbolic"},
    "r": {"name": "Reddit", "url": "https://www.reddit.com/search/?q={}", "icon": "user-bookmarks-symbolic"},
    "tr": {"name": "Google Translate", "url": "https://translate.google.com/?sl=auto&tl=en&text={}&op=translate", "icon": "accessories-dictionary-symbolic"},
}

def check_web_query(query: str):
    q = query.strip()
    if not q:
        return None

    # URL direct match
    if q.startswith("http://") or q.startswith("https://"):
        return {
            "type": "url",
            "title": f"Open {q}",
            "description": "Open website in default browser",
            "url": q,
            "icon": "web-browser-symbolic"
        }

    # Direct domain match e.g. github.com, youtube.com
    if re_domain := check_domain(q):
        return {
            "type": "url",
            "title": f"Visit {re_domain}",
            "description": "Open website in default browser",
            "url": f"https://{re_domain}",
            "icon": "web-browser-symbolic"
        }

    # Prefix search e.g. "g query", "yt song"
    parts = q.split(" ", 1)
    prefix = parts[0].lower()
    if prefix in PROVIDERS and len(parts) > 1 and parts[1].strip():
        search_term = parts[1].strip()
        provider = PROVIDERS[prefix]
        encoded = urllib.parse.quote(search_term)
        return {
            "type": "search",
            "title": f"Search {provider['name']} for '{search_term}'",
            "description": f"Perform search on {provider['name']}",
            "url": provider["url"].format(encoded),
            "icon": provider["icon"]
        }
    
    return None

def check_domain(text: str):
    text = text.lower()
    if "." in text and " " not in text and not text.endswith("."):
        parts = text.split(".")
        if len(parts) >= 2 and len(parts[-1]) >= 2 and parts[-1].isalpha():
            return text
    return None

def open_url(url: str):
    webbrowser.open(url)
