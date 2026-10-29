#!/usr/bin/env bash
# Remove Aura Launcher from the user's home directory.
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"

rm -rf "$PREFIX/share/aura-launcher"
rm -f  "$PREFIX/bin/aura-launcher"
rm -f  "$PREFIX/share/applications/org.aura.Launcher.desktop"
rm -f  "$PREFIX/share/icons/hicolor/scalable/apps/org.aura.Launcher.svg"
rm -rf "$HOME/.config/aura-launcher"
rm -f  "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/org.aura.Launcher.desktop"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$PREFIX/share/applications" 2>/dev/null || true

printf '\033[1;32m  ✓\033[0m Aura Launcher removed\n'
