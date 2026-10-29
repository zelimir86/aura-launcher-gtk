"""Smoke test: build the window, run a few queries, then quit."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from aura_launcher.app import AuraApplication


def run():
    app = AuraApplication()
    problems = []

    def after_start():
        win = app.window
        if win is None:
            problems.append("window not created")
            app.quit()
            return False

        for query in ["", "fire", "2+2*10", "g python gtk4", "terminal", "reboot", "https://example.com"]:
            win.entry.set_text(query)
            win._refresh()
            titles = [r["title"] for r in win.results]
            print(f"  query={query!r:26} -> {len(titles)} results: {titles[:4]}")

        print(f"\n  indexed apps: {len(win.indexer.apps)}")
        app.quit()
        return False

    def on_activate(_app):
        GLib.timeout_add(400, after_start)

    app.connect("activate", on_activate)
    app.run([])
    return problems


if __name__ == "__main__":
    issues = run()
    if issues:
        print("PROBLEMS:", issues)
        sys.exit(1)
    print("\nOK")
