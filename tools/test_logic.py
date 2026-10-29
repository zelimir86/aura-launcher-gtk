"""Logic tests that need no display — used by CI and local checks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aura_launcher.calculator import evaluate_math
from aura_launcher.web_search import check_web_query
from aura_launcher.system_actions import get_matching_actions, ACTIONS

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label} {detail}")
        failures.append(label)


print("calculator")
check("2+2*10 = 22", evaluate_math("2+2*10") == "22")
check("sqrt(144) = 12", evaluate_math("sqrt(144)") == "12")
check("2^10 = 1024", evaluate_math("2^10") == "1024")
check("(3+5)/2 = 4", evaluate_math("(3+5)/2") == "4")
check("bare number is not math", evaluate_math("5") is None)
check("word is not math", evaluate_math("firefox") is None)
check("empty is not math", evaluate_math("") is None)

print("web search")
check("url passes through", check_web_query("https://example.com")["type"] == "url")
check("bare domain becomes url", check_web_query("github.com")["url"] == "https://github.com")
check("google prefix", "google.com/search" in check_web_query("g gtk4 tutorial")["url"])
check("youtube prefix", "youtube.com" in check_web_query("yt lo-fi")["url"])
check("plain word is not a search", check_web_query("firefox") is None)

print("system actions")
check("reboot matches", get_matching_actions("reboot")[0]["id"] == "reboot")
check("shutdown matches", get_matching_actions("shutdown")[0]["id"] == "poweroff")
check("single letter ignored", get_matching_actions("g") == [])
check("unknown word matches nothing", get_matching_actions("qwertyuiop") == [])
check("every action has a command", all(a.get("command") for a in ACTIONS))

print("app index")
from aura_launcher.app_indexer import AppIndexer

indexer = AppIndexer()
check("apps are indexed", len(indexer.apps) > 0, f"({len(indexer.apps)} found)")
if indexer.apps:
    sample = indexer.apps[0]
    check("index entry has required keys",
          {"id", "display_name", "app_info", "gicon"} <= set(sample))
    check("empty query returns results", len(indexer.search("", limit=5)) > 0)
    name = sample["display_name"]
    check("app finds itself by name", any(a["id"] == sample["id"] for a in indexer.search(name, limit=50)))
check("unknown query returns nothing", indexer.search("zzzqqqxxx", limit=5) == [])

print()
if failures:
    print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
    sys.exit(1)

print("all checks passed")
