#!/usr/bin/env bash
# Install Aura Launcher into the user's home directory.
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
APP_DIR="$PREFIX/share/aura-launcher"
BIN_DIR="$PREFIX/bin"
ICON_DIR="$PREFIX/share/icons/hicolor/scalable/apps"
APPS_DIR="$PREFIX/share/applications"

SETUP_SHORTCUT=0
for arg in "$@"; do
    case "$arg" in
        --shortcut) SETUP_SHORTCUT=1 ;;
        -h|--help)
            echo "Usage: ./install.sh [--shortcut]"
            echo "  --shortcut   also bind Super+Space (Cinnamon) automatically"
            exit 0
            ;;
    esac
done

info()  { printf '\033[1;35m::\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
fail()  { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; }

# ---------------------------------------------------------------- deps
info "Checking dependencies"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is missing"
    exit 1
fi
ok "python3 $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"

if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>/dev/null; then
    fail "GTK4 Python bindings are missing."
    echo
    echo "  Install them first:"
    echo "    Debian/Ubuntu/Mint : sudo apt install python3-gi gir1.2-gtk-4.0"
    echo "    Fedora             : sudo dnf install python3-gobject gtk4"
    echo "    Arch               : sudo pacman -S python-gobject gtk4"
    exit 1
fi
ok "GTK4 bindings"

# ---------------------------------------------------------------- files
info "Installing to $APP_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
cp -r "$SOURCE_DIR/aura_launcher" "$APP_DIR/"
cp "$SOURCE_DIR/aura-launcher" "$APP_DIR/aura-launcher"
find "$APP_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
ok "application files"

info "Creating launcher command"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/aura-launcher" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$APP_DIR\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m aura_launcher "\$@"
EOF
chmod +x "$BIN_DIR/aura-launcher"
ok "$BIN_DIR/aura-launcher"

info "Installing icon and desktop entry"
mkdir -p "$ICON_DIR" "$APPS_DIR"
cp "$SOURCE_DIR/assets/org.aura.Launcher.svg" "$ICON_DIR/"
cp "$SOURCE_DIR/assets/org.aura.Launcher.desktop" "$APPS_DIR/"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" 2>/dev/null || true
ok "icon + desktop entry"

# ---------------------------------------------------------------- shortcut
setup_shortcut() {
    local cmd="$BIN_DIR/aura-launcher"

    if ! command -v gsettings >/dev/null 2>&1; then
        fail "gsettings not found — bind the shortcut manually"
        return
    fi
    local schemas
    schemas="$(gsettings list-schemas 2>/dev/null || true)"
    if ! grep -qx "org.cinnamon.desktop.keybindings" <<< "$schemas"; then
        info "This desktop is not Cinnamon — bind the shortcut manually"
        return
    fi

    info "Binding Super+Space to Aura Launcher"

    local idx list
    list="$(gsettings get org.cinnamon.desktop.keybindings custom-list)"

    # Reuse an existing "Aura Launcher" entry, otherwise take the first free slot.
    idx=""
    for i in $(seq 0 29); do
        local path="/org/cinnamon/desktop/keybindings/custom-keybindings/custom$i/"
        local name
        name="$(gsettings get "org.cinnamon.desktop.keybindings.custom-keybinding:$path" name 2>/dev/null || true)"
        if [ "$name" = "'Aura Launcher'" ]; then
            idx="$i"
            break
        fi
    done

    if [ -z "$idx" ]; then
        for i in $(seq 0 29); do
            case "$list" in
                *"custom$i"*) ;;
                *) idx="$i"; break ;;
            esac
        done
    fi

    if [ -z "$idx" ]; then
        fail "no free custom shortcut slot"
        return
    fi

    local path="/org/cinnamon/desktop/keybindings/custom-keybindings/custom$idx/"
    gsettings set "org.cinnamon.desktop.keybindings.custom-keybinding:$path" name "Aura Launcher"
    gsettings set "org.cinnamon.desktop.keybindings.custom-keybinding:$path" command "$cmd"
    gsettings set "org.cinnamon.desktop.keybindings.custom-keybinding:$path" binding "['<Super>space']"

    # Make sure the slot is registered in the global custom-list.
    case "$list" in
        *"custom$idx"*) ;;
        *)
            local new_list
            new_list="$(python3 - "$idx" "$list" <<'PY'
import ast, sys
idx, raw = sys.argv[1], sys.argv[2]
items = [i for i in ast.literal_eval(raw) if i != "__dummy__"]
items.append(f"custom{idx}")
items.append("__dummy__")
print("[" + ", ".join(f"'{i}'" for i in items) + "]")
PY
)"
            gsettings set org.cinnamon.desktop.keybindings custom-list "$new_list"
            ;;
    esac

    ok "Super+Space → $cmd"
}

# ---------------------------------------------------------------- summary
echo
if [ "$SETUP_SHORTCUT" -eq 1 ]; then
    setup_shortcut
fi

info "Done!"
echo
echo "  Run it:        aura-launcher"
echo "  Or from menu:  Aura Launcher"
echo
echo "  Make sure $BIN_DIR is in your PATH."
echo
echo "  ── Keyboard shortcut (Cinnamon) ─────────────────────────────"
echo "  System Settings → Keyboard → Shortcuts → Custom Shortcuts"
echo "    Name    : Aura Launcher"
echo "    Command : aura-launcher"
echo "    Keybind : Super+Space  (or any free combo)"
echo
echo "  ── Keyboard shortcut (GNOME) ────────────────────────────────"
echo "  Settings → Keyboard → Custom Shortcuts → +"
echo "    Command : aura-launcher"
echo "    Keybind : Super+Space"
echo
