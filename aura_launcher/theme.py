"""Detect the system dark/light preference and watch for changes."""

import os
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio


def _schema_source():
    try:
        return Gio.SettingsSchemaSource.get_default()
    except Exception:
        return None


def _adw_style_manager():
    """libadwaita's StyleManager, when available, knows the desktop preference."""
    try:
        gi.require_version("Adw", "1")
        from gi.repository import Adw
    except Exception:
        return None
    try:
        return Adw.StyleManager.get_default()
    except Exception:
        return None


class ThemeWatcher:
    """Reports whether the desktop currently asks for a dark appearance.

    Several sources are consulted because desktops expose this differently:
    GNOME uses the ``color-scheme`` key, Cinnamon/MATE encode it in the theme
    name ("Mint-Y-Dark"), and libadwaita mirrors the portal preference.
    """

    def __init__(self, on_change):
        self._on_change = on_change
        self._settings = []
        source = _schema_source()
        self._adw = _adw_style_manager()
        self._override = os.environ.get("AURA_THEME", "").strip().lower()

        if self._adw is not None:
            self._adw.connect("notify::dark", self._changed)

        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            gtk_settings.connect("notify::gtk-application-prefer-dark-theme", self._changed)

        for schema_id in (
            "org.cinnamon.desktop.interface",
            "org.gnome.desktop.interface",
            "org.mate.interface",
            "org.xfce.interface",
        ):
            schema = source.lookup(schema_id, True) if source is not None else None
            if schema is None:
                continue
            settings = Gio.Settings.new_full(schema, None, None)
            self._settings.append(settings)
            for key in ("gtk-theme", "color-scheme"):
                try:
                    if settings.settings_schema.has_key(key):
                        settings.connect(f"changed::{key}", self._changed)
                except Exception:
                    pass

    def _changed(self, *_args):
        self._on_change(self.is_dark())

    def is_dark(self) -> bool:
        if self._override in ("dark", "light"):
            return self._override == "dark"

        # 1. Explicit colour-scheme key (GNOME 42+, KDE, XFCE 4.18+)
        for settings in self._settings:
            try:
                if not settings.settings_schema.has_key("color-scheme"):
                    continue
                scheme = settings.get_string("color-scheme")
            except Exception:
                continue
            if scheme == "prefer-dark":
                return True
            if scheme in ("prefer-light", "default"):
                return False

        # 2. Theme name carries the answer on Cinnamon / MATE
        for settings in self._settings:
            try:
                name = settings.get_string("gtk-theme")
            except Exception:
                continue
            if name:
                return "dark" in name.lower()

        # 3. libadwaita / GTK fallbacks
        if self._adw is not None:
            return bool(self._adw.get_dark())

        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            return bool(gtk_settings.get_property("gtk-application-prefer-dark-theme"))

        return True
