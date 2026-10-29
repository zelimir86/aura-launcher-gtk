#!/usr/bin/env bash
# Build an RPM package for Aura Launcher.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(grep -oP '__version__ = "\K[^"]+' "$ROOT/aura_launcher/__init__.py")"
NAME="aura-launcher"
TOPDIR="$ROOT/build/rpm"

info() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }

if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "rpmbuild not found. Install it first:" >&2
    echo "  Debian/Ubuntu: sudo apt install rpm" >&2
    echo "  Fedora:        sudo dnf install rpm-build" >&2
    exit 1
fi

info "Building ${NAME} ${VERSION} (.rpm)"

rm -rf "$TOPDIR"
mkdir -p "$TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Source tarball with the layout the spec expects
STAGE="$TOPDIR/${NAME}-${VERSION}"
mkdir -p "$STAGE"
cp -r "$ROOT/aura_launcher" "$STAGE/"
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
cp "$ROOT/LICENSE" "$ROOT/README.md" "$STAGE/"
cp -r "$ROOT/assets" "$STAGE/"
tar czf "$TOPDIR/SOURCES/${NAME}-${VERSION}.tar.gz" -C "$TOPDIR" "${NAME}-${VERSION}"

cp "$ROOT/packaging/aura-launcher.spec" "$TOPDIR/SPECS/"

rpmbuild -bb \
    --define "_topdir $TOPDIR" \
    --define "version $VERSION" \
    "$TOPDIR/SPECS/${NAME}.spec" >/dev/null

find "$TOPDIR/RPMS" -name '*.rpm' -exec cp {} "$ROOT/build/" \;

ok "$(find "$ROOT/build" -maxdepth 1 -name '*.rpm' | head -1)"
