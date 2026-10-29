# Build with packaging/build-rpm.sh — it passes the version from
# aura_launcher/__init__.py. The fallback below only matters for a manual
# rpmbuild invocation.
%{!?version:%global version 1.1.0}

Name:           aura-launcher
Version:        %{version}
Release:        1%{?dist}
Summary:        Modern GTK4 application launcher for Linux
License:        MIT
URL:            https://github.com/zelimir86/aura-launcher-gtk
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4

%description
Aura Launcher searches .desktop files, evaluates math expressions, performs
web searches, runs system actions and follows the desktop dark/light
preference. It runs as a single background instance and opens instantly from
a keyboard shortcut.

%prep
%setup -q

%build
# Pure Python: nothing to compile.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_datadir}/aura-launcher
install -d %{buildroot}%{_datadir}/applications
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

cp -r aura_launcher %{buildroot}%{_datadir}/aura-launcher/
find %{buildroot}%{_datadir}/aura-launcher -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > %{buildroot}%{_bindir}/aura-launcher <<'LAUNCHER'
#!/bin/sh
export PYTHONPATH="__SHAREDIR__/aura-launcher${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m aura_launcher "$@"
LAUNCHER
sed -i 's|__SHAREDIR__|%{_datadir}|' %{buildroot}%{_bindir}/aura-launcher
chmod 755 %{buildroot}%{_bindir}/aura-launcher

install -m 644 assets/org.aura.Launcher.desktop %{buildroot}%{_datadir}/applications/
install -m 644 assets/org.aura.Launcher.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%{_bindir}/aura-launcher
%{_datadir}/aura-launcher
%{_datadir}/applications/org.aura.Launcher.desktop
%{_datadir}/icons/hicolor/scalable/apps/org.aura.Launcher.svg
%license LICENSE
%doc README.md

%changelog
* Thu Oct 29 2026 Želimir Stevanović <zelimir86@users.noreply.github.com> - 1.1.0-1
- Initial package
