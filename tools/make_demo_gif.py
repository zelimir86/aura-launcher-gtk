"""Render a scripted demo of the launcher into docs/demo.gif.

Frames are painted offscreen with Gtk.WidgetPaintable, so the result is a real
render of the UI rather than a screen capture (which needs a compositor that
supports wlr-screencopy).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["AURA_APP_ID"] = "org.aura.LauncherDemo"
os.environ.setdefault("AURA_THEME", "light")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")

from gi.repository import Gtk, GLib, Graphene
from PIL import Image

from aura_launcher.app import AuraApplication

FRAME_DIR = "/tmp/aura_demo_frames"
OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "demo.gif"
)
BACKDROP = (227, 230, 236, 255)

# (query, milliseconds to hold the frame)
SCRIPT = [
    ("", 900),
    ("f", 260),
    ("fi", 260),
    ("fir", 260),
    ("fire", 1200),
    ("2^10 + sqrt(144)", 1400),
    ("yt lo-fi beats", 1400),
    ("", 800),
]

captured = []


def capture(win, index):
    width, height = win.get_width(), win.get_height()
    paintable = Gtk.WidgetPaintable.new(win)
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, width, height)
    node = snapshot.to_node()
    renderer = win.get_renderer()
    if renderer is None or node is None:
        return False
    texture = renderer.render_texture(node, Graphene.Rect().init(0, 0, width, height))
    path = os.path.join(FRAME_DIR, f"frame_{index:02d}.png")
    texture.save_to_png(path)
    captured.append(path)
    return False


def run_step(app, index):
    if index >= len(SCRIPT):
        app.quit()
        return False

    win = app.window
    query, hold = SCRIPT[index]
    win.entry.set_text(query)
    win._refresh()

    def after_layout():
        capture(win, index)
        GLib.timeout_add(hold, run_step, app, index + 1)
        return False

    GLib.timeout_add(200, after_layout)
    return False


def build_gif():
    os.makedirs(FRAME_DIR, exist_ok=True)
    images = [Image.open(p).convert("RGBA") for p in captured]
    if not images:
        raise SystemExit("no frames captured")

    width = max(im.width for im in images)
    height = max(im.height for im in images)

    composed = []
    for im in images:
        canvas = Image.new("RGBA", (width, height), BACKDROP)
        canvas.alpha_composite(im, ((width - im.width) // 2, (height - im.height) // 2))
        composed.append(canvas.convert("RGB"))

    composed[0].save(
        OUT_PATH,
        save_all=True,
        append_images=composed[1:],
        duration=[hold for _, hold in SCRIPT],
        loop=0,
        optimize=True,
    )
    print(f"saved {OUT_PATH} ({width}x{height}, {len(composed)} frames)")


def main():
    os.makedirs(FRAME_DIR, exist_ok=True)
    for stale in os.listdir(FRAME_DIR):
        os.remove(os.path.join(FRAME_DIR, stale))

    app = AuraApplication()

    def on_activate(_app):
        GLib.timeout_add(400, run_step, app, 0)

    app.connect("activate", on_activate)
    app.run([])
    build_gif()


if __name__ == "__main__":
    main()
