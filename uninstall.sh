#!/usr/bin/env bash
# Remove Aura Launcher from the user's home directory.
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"

ok() { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }

# Rebuild the icon cache for a hicolor tree. Leaving a stale cache behind keeps
# listing icons that no longer exist, and GTK then fails to load them instead
# of falling back to the system theme (icon shows up blank).
refresh_icon_cache() {
    local dir="$1"
    [ -d "$dir" ] || return 0
    if command -v gtk4-update-icon-cache >/dev/null 2>&1; then
        gtk4-update-icon-cache -f -t "$dir" >/dev/null 2>&1 || true
    elif command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$dir" >/dev/null 2>&1 || true
    fi
}

rm -rf "$PREFIX/share/aura-launcher"
rm -f  "$PREFIX/bin/aura-launcher"
rm -f  "$PREFIX/share/applications/org.aura.Launcher.desktop"
rm -f  "$PREFIX/share/icons/hicolor/scalable/apps/org.aura.Launcher.svg"
rm -rf "$HOME/.config/aura-launcher"
rm -f  "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/org.aura.Launcher.desktop"

refresh_icon_cache "$PREFIX/share/icons/hicolor"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$PREFIX/share/applications" 2>/dev/null || true

ok "Aura Launcher removed"
