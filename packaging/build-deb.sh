#!/usr/bin/env bash
# Build a Debian package for Aura Launcher.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep -oP '__version__ = "\K[^"]+' "$ROOT/aura_launcher/__init__.py")"
PKG="aura-launcher"
ARCH="all"
STAGE="$ROOT/build/deb/${PKG}_${VERSION}_${ARCH}"
OUT="$ROOT/build"

info() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }

info "Building ${PKG} ${VERSION} (.deb)"

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN"
mkdir -p "$STAGE/usr/bin"
mkdir -p "$STAGE/usr/share/${PKG}"
mkdir -p "$STAGE/usr/share/applications"
mkdir -p "$STAGE/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$STAGE/usr/share/doc/${PKG}"
mkdir -p "$STAGE/usr/share/man/man1"

# Application files
cp -r "$ROOT/aura_launcher" "$STAGE/usr/share/${PKG}/"
find "$STAGE/usr/share/${PKG}" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Launcher command
cat > "$STAGE/usr/bin/aura-launcher" <<'EOF'
#!/bin/sh
export PYTHONPATH="/usr/share/aura-launcher${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m aura_launcher "$@"
EOF
chmod 755 "$STAGE/usr/bin/aura-launcher"

# Desktop entry and icon
cp "$ROOT/assets/org.aura.Launcher.desktop" "$STAGE/usr/share/applications/"
cp "$ROOT/assets/org.aura.Launcher.svg" "$STAGE/usr/share/icons/hicolor/scalable/apps/"
chmod 644 "$STAGE/usr/share/applications/org.aura.Launcher.desktop"

# Documentation
cp "$ROOT/LICENSE" "$STAGE/usr/share/doc/${PKG}/copyright"
cp "$ROOT/README.md" "$STAGE/usr/share/doc/${PKG}/README.md"
gzip -9n -c "$ROOT/packaging/changelog" > "$STAGE/usr/share/doc/${PKG}/changelog.gz"
gzip -9n -c "$ROOT/packaging/aura-launcher.1" > "$STAGE/usr/share/man/man1/aura-launcher.1.gz"

# Normalise permissions so lintian stays quiet
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +
chmod 755 "$STAGE/usr/bin/aura-launcher"

SIZE="$(du -sk "$STAGE" | cut -f1)"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: ${PKG}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Želimir Stevanović <zelimir86@users.noreply.github.com>
Installed-Size: ${SIZE}
Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-4.0
Recommends: gir1.2-gtk4layershell-1.0
Homepage: https://github.com/zelimir86/aura-launcher-gtk
Description: modern GTK4 application launcher for Linux
 Aura Launcher searches .desktop files, evaluates math expressions,
 performs web searches, runs system actions and follows the desktop
 dark/light preference.
 .
 It runs as a single background instance and opens instantly from a
 keyboard shortcut.
EOF

mkdir -p "$OUT"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT/${PKG}_${VERSION}_${ARCH}.deb" >/dev/null

ok "$OUT/${PKG}_${VERSION}_${ARCH}.deb"
dpkg-deb -I "$OUT/${PKG}_${VERSION}_${ARCH}.deb" | sed -n '1,12p'
