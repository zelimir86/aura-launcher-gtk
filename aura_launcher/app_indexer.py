import json
import os
import subprocess
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gdk, Gtk, GLib

USAGE_FILE = os.path.expanduser("~/.config/aura-launcher/usage.json")

class AppIndexer:
    def __init__(self):
        self.apps = []
        self.usage_counts = self._load_usage()
        self.reload()

    def _load_usage(self) -> dict:
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_usage(self):
        try:
            os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
            with open(USAGE_FILE, 'w') as f:
                json.dump(self.usage_counts, f)
        except Exception:
            pass

    def increment_usage(self, app_id: str):
        self.usage_counts[app_id] = self.usage_counts.get(app_id, 0) + 1
        self._save_usage()

    def reload(self):
        self.apps = []
        all_apps = Gio.AppInfo.get_all()
        seen_ids = set()

        for app_info in all_apps:
            if not app_info.should_show():
                continue
            
            app_id = app_info.get_id() or app_info.get_executable() or app_info.get_name()
            if not app_id or app_id in seen_ids:
                continue
            seen_ids.add(app_id)

            name = app_info.get_name() or ""
            display_name = app_info.get_display_name() or name
            description = app_info.get_description() or ""
            executable = app_info.get_executable() or ""
            keywords = app_info.get_keywords() or []
            categories = app_info.get_categories() or ""
            
            # Control-panel entries are useful when searched for, but they
            # clutter the default "recent apps" view.
            is_panel = (
                "Settings" in categories
                or "X-GNOME-Settings-Panel" in categories
                or app_id.startswith("cinnamon-settings")
            )
            
            # Icon
            gicon = app_info.get_icon()

            self.apps.append({
                "id": app_id,
                "app_info": app_info,
                "name": name,
                "display_name": display_name,
                "description": description,
                "executable": executable,
                "keywords": " ".join(keywords).lower(),
                "categories": categories,
                "is_panel": is_panel,
                "gicon": gicon,
                "usage": self.usage_counts.get(app_id, 0)
            })

    def search(self, query: str, limit: int = 12):
        q = query.strip().lower()
        if not q:
            # Return top apps sorted by usage, then alphabetically. Settings
            # panels are pushed to the end so they do not dominate the view.
            sorted_apps = sorted(
                self.apps,
                key=lambda a: (a["is_panel"], -a["usage"], a["display_name"].lower()),
            )
            return sorted_apps[:limit]

        results = []
        for app in self.apps:
            score = self._calculate_score(app, q)
            if score > 0:
                results.append((score, app))

        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:limit]]

    def _calculate_score(self, app: dict, q: str) -> float:
        score = 0.0
        name = app["display_name"].lower()
        exec_name = app["executable"].lower()
        desc = app["description"].lower()
        keywords = app["keywords"]

        # Exact match
        if name == q or exec_name == q:
            score += 1000.0

        # Starts with
        elif name.startswith(q) or exec_name.startswith(q):
            score += 500.0 + (100.0 / (len(name) + 1))

        # Word boundary match
        elif f" {q}" in f" {name}" or f" {q}" in f" {exec_name}":
            score += 300.0

        # Substring in name or executable
        elif q in name or q in exec_name:
            score += 150.0

        # Substring in keywords
        elif q in keywords:
            score += 80.0

        # Substring in description
        elif q in desc:
            score += 40.0

        # Acronym match (e.g., 'vs' -> Visual Studio Code, 'ff' -> Firefox)
        else:
            acronym = "".join([w[0] for w in name.split() if w])
            if acronym and acronym.startswith(q):
                score += 200.0

        if score > 0:
            # Boost score based on past launch usage
            score += min(app["usage"] * 10.0, 200.0)

        return score
