"""Application object and entry point for Aura Launcher."""

import os
import sys
import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gio, GLib

from . import __app_id__, __version__
from .theme import ThemeWatcher
from .window import AuraWindow, apply_theme


class AuraApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=os.environ.get("AURA_APP_ID", __app_id__),
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.window = None
        self.theme = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.theme = ThemeWatcher(self._on_theme_changed)
        apply_theme(self.theme.is_dark())

    def _on_theme_changed(self, dark):
        apply_theme(dark)
        if self.window is not None:
            self.window.queue_draw()

    def do_activate(self):
        if self.window is None:
            self.window = AuraWindow(self)
        self.window.present_launcher()

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]

        if "--version" in args or "-v" in args:
            print(f"Aura Launcher {__version__}")
            return 0

        if "--quit" in args or "-q" in args:
            self.quit()
            return 0

        self.activate()
        return 0


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)

    # Answer --version locally: with a background instance running, the
    # command line would otherwise be forwarded over D-Bus and print nothing.
    if "--version" in argv[1:] or "-v" in argv[1:]:
        print(f"Aura Launcher {__version__}")
        return 0

    app = AuraApplication()
    return app.run(argv)


if __name__ == "__main__":
    sys.exit(main())
