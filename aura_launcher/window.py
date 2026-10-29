"""Aura Launcher — main window and UI logic."""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Gdk, GLib, Gio, Pango

from .app_indexer import AppIndexer
from .calculator import evaluate_math
from .web_search import check_web_query, open_url
from .system_actions import get_matching_actions, execute_action

BASE_DIR = os.path.dirname(__file__)
CSS_PATH = os.path.join(BASE_DIR, "style.css")

# Tallest the result list may grow before it starts scrolling.
MAX_LIST_HEIGHT = 470

_provider = None


def apply_theme(dark: bool):
    """(Re)build the stylesheet for the requested appearance.

    The palette file is prepended to the layout file so every @colour is
    defined before it is referenced.
    """
    global _provider
    display = Gdk.Display.get_default()
    if display is None:
        return

    theme_file = "theme-dark.css" if dark else "theme-light.css"
    with open(os.path.join(BASE_DIR, theme_file), encoding="utf-8") as fh:
        palette = fh.read()
    with open(CSS_PATH, encoding="utf-8") as fh:
        layout = fh.read()

    if _provider is None:
        _provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            display, _provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    _provider.load_from_string(palette + "\n" + layout)


def _make_icon(result, size=26):
    """Build a Gtk.Image from a result descriptor."""
    img = Gtk.Image()
    gicon = result.get("gicon")
    if gicon is not None:
        img.set_from_gicon(gicon)
    else:
        img.set_from_icon_name(result.get("icon_name") or "application-x-executable-symbolic")
    img.set_pixel_size(size)
    return img


class ResultRow(Gtk.ListBoxRow):
    def __init__(self, result):
        super().__init__()
        self.result = result

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        box.add_css_class("aura-row")

        icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        icon_box.set_valign(Gtk.Align.CENTER)
        icon_box.set_halign(Gtk.Align.CENTER)
        icon_box.add_css_class("aura-icon-box")
        if result.get("accent"):
            icon_box.add_css_class("accent")
        icon_box.append(_make_icon(result))
        box.append(icon_box)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_valign(Gtk.Align.CENTER)
        text_box.set_hexpand(True)

        title = Gtk.Label(label=result["title"])
        title.set_halign(Gtk.Align.START)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("aura-row-title")
        text_box.append(title)

        subtitle_text = result.get("subtitle") or ""
        if subtitle_text:
            subtitle = Gtk.Label(label=subtitle_text)
            subtitle.set_halign(Gtk.Align.START)
            subtitle.set_ellipsize(Pango.EllipsizeMode.END)
            subtitle.add_css_class("aura-row-subtitle")
            text_box.append(subtitle)

        box.append(text_box)

        badge_text = result.get("badge")
        if badge_text:
            badge = Gtk.Label(label=badge_text)
            badge.set_valign(Gtk.Align.CENTER)
            badge.add_css_class("aura-badge")
            if result.get("kind") == "calc":
                badge.add_css_class("calc")
            box.append(badge)

        self.set_child(box)


class AuraWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.indexer = AppIndexer()
        self.results = []
        self._debounce_id = 0
        self._closing = False
        self._layer = None

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(780, -1)
        self.add_css_class("aura-window")
        self.set_title("Aura Launcher")

        # Outer margin so the drop shadow has room to breathe.
        outer = Gtk.Box()
        outer.set_margin_top(0)
        outer.set_margin_bottom(0)
        outer.set_margin_start(0)
        outer.set_margin_end(0)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("aura-card")
        card.set_overflow(Gtk.Overflow.HIDDEN)
        outer.append(card)
        self.set_child(outer)

        # ---- search row ----
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        search_box.add_css_class("aura-search-box")
        self.search_box = search_box

        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_icon.set_pixel_size(22)
        search_icon.set_valign(Gtk.Align.CENTER)
        search_icon.add_css_class("aura-search-icon")
        search_box.append(search_icon)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search apps, calculate, search the web…")
        self.entry.set_hexpand(True)
        self.entry.set_has_frame(False)
        self.entry.add_css_class("aura-entry")
        self.entry.connect("changed", self._on_changed)
        self.entry.connect("activate", self._on_activate_entry)
        search_box.append(self.entry)

        card.append(search_box)

        divider = Gtk.Box()
        divider.add_css_class("aura-divider")
        card.append(divider)

        # ---- results ----
        scroll = Gtk.ScrolledWindow()
        scroll.add_css_class("aura-scroll")
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_propagate_natural_height(True)
        scroll.set_max_content_height(MAX_LIST_HEIGHT)
        self.scroll = scroll

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("aura-list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.set_activate_on_single_click(False)
        self.listbox.connect("row-activated", self._on_row_activated)
        scroll.set_child(self.listbox)
        card.append(scroll)

        # small breathing room between the last row and the footer
        spacer_gap = Gtk.Box()
        spacer_gap.set_size_request(-1, 4)
        card.append(spacer_gap)

        # ---- footer ----
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        footer.add_css_class("aura-footer")
        self.footer = footer

        for key, label in (("↑↓", "Navigate"), ("↵", "Open"), ("Esc", "Close")):
            hint_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            key_label = Gtk.Label(label=key)
            key_label.add_css_class("aura-key")
            hint_box.append(key_label)
            text = Gtk.Label(label=label)
            text.add_css_class("aura-hint")
            hint_box.append(text)
            footer.append(hint_box)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        footer.append(spacer)

        brand = Gtk.Label(label="AURA")
        brand.add_css_class("aura-brand")
        footer.append(brand)

        card.append(footer)

        # ---- keyboard handling ----
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

        self.connect("notify::is-active", self._on_active_changed)

        self._setup_layer_shell()
        self._refresh()

    # ------------------------------------------------------------------
    # search pipeline
    # ------------------------------------------------------------------

    def _on_changed(self, _entry):
        if self._debounce_id:
            GLib.source_remove(self._debounce_id)
        self._debounce_id = GLib.timeout_add(55, self._refresh)

    def _refresh(self):
        self._debounce_id = 0
        query = self.entry.get_text().strip()
        results = []

        if query:
            # 1. calculator
            calc = evaluate_math(query)
            if calc is not None:
                results.append({
                    "kind": "calc",
                    "title": calc,
                    "subtitle": f"= {query}",
                    "badge": "COPY",
                    "icon_name": "accessories-calculator-symbolic",
                    "accent": True,
                    "action": lambda c=calc: self._copy(c),
                })

            # 2. system actions
            for act in get_matching_actions(query):
                results.append({
                    "kind": "action",
                    "title": act["title"],
                    "subtitle": act["description"],
                    "badge": "SYSTEM",
                    "icon_name": act["icon"],
                    "action": lambda a=act: execute_action(a),
                })

        # 3. applications
        apps = self.indexer.search(query, limit=9 if query else 10)
        for app in apps:
            results.append({
                "kind": "app",
                "title": app["display_name"],
                "subtitle": app["description"] or app["executable"],
                "badge": "APP",
                "gicon": app["gicon"],
                "action": lambda a=app: self._launch_app(a),
            })

        # 4. web search / url
        if query:
            web = check_web_query(query)
            if web is not None:
                results.append({
                    "kind": "web",
                    "title": web["title"],
                    "subtitle": web["description"],
                    "badge": "WEB",
                    "icon_name": web["icon"],
                    "action": lambda u=web["url"]: open_url(u),
                })

        self.results = results
        self._render(results)

    def _render(self, results):
        child = self.listbox.get_first_child()
        while child is not None:
            self.listbox.remove(child)
            child = self.listbox.get_first_child()

        if not results:
            empty = Gtk.ListBoxRow()
            empty.set_selectable(False)
            empty.set_activatable(False)
            label = Gtk.Label(label="No results")
            label.add_css_class("aura-empty")
            empty.set_child(label)
            self.listbox.append(empty)
            return

        rows = []
        for result in results:
            row = ResultRow(result)
            self.listbox.append(row)
            rows.append(row)

        # Drop rows that would be clipped by the bottom edge, so the launcher
        # never shows a half-visible entry.
        available = self._available_list_height()
        if available > 0:
            while len(rows) > 1:
                natural = self.listbox.measure(Gtk.Orientation.VERTICAL, self._content_width())[1]
                if natural <= available:
                    break
                self.listbox.remove(rows.pop())

        self.results = self.results[: len(rows)]

        if rows:
            self.listbox.select_row(rows[0])

        if self._layer is not None:
            GLib.idle_add(self._position_after_layout)

    def _position_after_layout(self):
        self._position_layer()
        return False

    def _content_width(self):
        return max(self.get_width() - 2, 360)

    def _available_list_height(self):
        return MAX_LIST_HEIGHT

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------

    def _run_result(self, result):
        action = result.get("action")
        if action is None:
            return
        self.hide()
        GLib.idle_add(self._invoke, action)

    def _invoke(self, action):
        try:
            action()
        except Exception as exc:  # pragma: no cover - runtime guard
            print(f"[aura] action failed: {exc}")
        return False

    def _launch_app(self, app):
        try:
            context = Gdk.Display.get_default().get_app_launch_context()
            app["app_info"].launch([], context)
            self.indexer.increment_usage(app["id"])
        except Exception as exc:
            print(f"[aura] failed to launch {app['id']}: {exc}")

    def _copy(self, text):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    def _on_row_activated(self, _listbox, row):
        if isinstance(row, ResultRow):
            self._run_result(row.result)

    def _on_activate_entry(self, _entry):
        row = self.listbox.get_selected_row()
        if isinstance(row, ResultRow):
            self._run_result(row.result)
        elif self.results:
            self._run_result(self.results[0])

    def _move_selection(self, delta):
        row = self.listbox.get_selected_row()
        if row is None:
            index = 0
        else:
            index = row.get_index() + delta
        count = len(self.results)
        if count == 0:
            return
        index = max(0, min(index, count - 1))
        target = self.listbox.get_row_at_index(index)
        if target is not None and isinstance(target, ResultRow):
            self.listbox.select_row(target)
            target.grab_focus()

    def _on_key_pressed(self, _controller, keyval, _keycode, state):
        if keyval == Gdk.KEY_Escape:
            if self.entry.get_text():
                self.entry.set_text("")
            else:
                self.hide()
            return True
        if keyval == Gdk.KEY_Down:
            self._move_selection(1)
            return True
        if keyval == Gdk.KEY_Up:
            self._move_selection(-1)
            return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            row = self.listbox.get_selected_row()
            if isinstance(row, ResultRow):
                self._run_result(row.result)
            return True
        if keyval == Gdk.KEY_Tab:
            self._move_selection(1 if not (state & Gdk.ModifierType.SHIFT_MASK) else -1)
            return True
        return False

    def _on_active_changed(self, *_args):
        if not self.get_property("is-active") and not self._closing:
            self.hide()

    # ------------------------------------------------------------------
    # layer shell (opt-in)
    # ------------------------------------------------------------------

    def _setup_layer_shell(self):
        """Opt-in wlr-layer-shell support for Wayland compositors.

        Off by default because it changes how the compositor treats the
        surface. Enable with AURA_LAYER_SHELL=1 once it has been verified on
        the target system. Any failure falls back to a normal window.
        """
        if os.environ.get("AURA_LAYER_SHELL", "").strip().lower() not in ("1", "true", "yes"):
            return False
        if not os.environ.get("WAYLAND_DISPLAY"):
            return False
        try:
            gi.require_version("Gtk4LayerShell", "1.0")
            from gi.repository import Gtk4LayerShell as layer
        except Exception:
            return False

        try:
            if hasattr(layer, "is_supported") and not layer.is_supported():
                return False
            layer.init_for_window(self)
            layer.set_layer(self, layer.Layer.OVERLAY)
            layer.set_keyboard_mode(self, layer.KeyboardMode.ON_DEMAND)
            layer.set_anchor(self, layer.Edge.TOP, True)
            layer.set_anchor(self, layer.Edge.LEFT, True)
        except Exception as exc:
            print(f"[aura] layer shell unavailable: {exc}")
            return False

        self._layer = layer
        return True

    def _position_layer(self):
        """Centre horizontally and drop the surface near the top of the screen."""
        if self._layer is None:
            return
        try:
            display = Gdk.Display.get_default()
            monitors = display.get_monitors() if display else None
            monitor = monitors.get_item(0) if monitors and monitors.get_n_items() else None
            geometry = monitor.get_geometry() if monitor else None

            width = self.get_width() or 780
            if geometry is not None:
                left = max((geometry.width - width) // 2, 0)
                top = max(int(geometry.height * 0.14), 0)
            else:
                left, top = 0, 0

            self._layer.set_margin(self, self._layer.Edge.LEFT, left)
            self._layer.set_margin(self, self._layer.Edge.TOP, top)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def present_launcher(self):
        self.entry.set_text("")
        self._refresh()
        self.present()
        self._position_layer()
        self.entry.grab_focus()

    def close_launcher(self):
        self._closing = True
        self.hide()
        self._closing = False
