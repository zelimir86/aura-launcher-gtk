"""Render the launcher window to a PNG (used for previews/docs)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")

from gi.repository import Gtk, GLib, Graphene

os.environ.setdefault("AURA_APP_ID", "org.aura.LauncherPreview")

from aura_launcher.app import AuraApplication


def main(query, out_path):
    app = AuraApplication()

    def on_activate(_app):
        GLib.timeout_add(150, setup, app)

    def setup(_app):
        win = app.window
        win.entry.set_text(query)
        win._refresh()
        GLib.timeout_add(900, capture, app, win)
        return False

    def capture(_app, win):
        width, height = win.get_width(), win.get_height()
        paintable = Gtk.WidgetPaintable.new(win)
        snapshot = Gtk.Snapshot()
        paintable.snapshot(snapshot, width, height)
        node = snapshot.to_node()
        renderer = win.get_renderer()
        rect = Graphene.Rect().init(0, 0, width, height)
        texture = renderer.render_texture(node, rect)
        texture.save_to_png(out_path)
        print(f"saved {out_path} ({width}x{height})")
        app.quit()
        return False

    app.connect("activate", on_activate)
    return app.run([])


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/aura.png"
    sys.exit(main(query, out))
