# Aura Launcher

[![CI](https://github.com/zelimir86/aura-launcher-gtk/actions/workflows/ci.yml/badge.svg)](https://github.com/zelimir86/aura-launcher-gtk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Moderan aplikacijski launcher za Linux — kao Ulauncher, ali sa čistim savremenim
interfejsom, pametnim pretraživanjem, ugrađenim kalkulatorom i automatskom
tamnom/svetlom temom.

![Aura Launcher demo](docs/demo.gif)

<p align="center">
  <img src="docs/preview.png" width="49%" alt="Aura Launcher — dark theme">
  <img src="docs/preview_light.png" width="49%" alt="Aura Launcher — light theme">
</p>

---

## Karakteristike

| Funkcija | Opis |
|---|---|
| **Pretraga aplikacija** | Indeksira sve `.desktop` fajlove, pametno rangira po nazivu, opisu, ključnim rečima i skraćenicama |
| **Učenje navika** | Pamti koliko često pokrećeš koju aplikaciju i izbacuje je na vrh liste |
| **Kalkulator** | Ukucaj `2^10 + sqrt(144)` i rezultat se pojavi odmah; `Enter` kopira rezultat |
| **Veb pretraga** | `g nešto`, `ddg nešto`, `yt nešto`, `gh nešto`, `wiki nešto` |
| **Otvori URL** | Nalepi `https://...` ili samo `github.com` |
| **Sistemske akcije** | `lock`, `reboot`, `shutdown`, `logout`, `sleep` |
| **Dinamička visina** | Prozor se skuplja i širi u zavisnosti od broja rezultata |
| **Tamna i svetla tema** | Automatski prati dark/light podešavanje sistema, u realnom vremenu |
| **Tastatura** | `↑` `↓` navigacija, `Enter` otvara, `Esc` briše tekst / zatvara |

## Zahtevi

- Python 3.9+
- GTK 4 + PyGObject

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install python3-gi gir1.2-gtk-4.0

# Fedora
sudo dnf install python3-gobject gtk4

# Arch
sudo pacman -S python-gobject gtk4
```

## Instalacija

```bash
chmod +x install.sh uninstall.sh
./install.sh              # samo instaliraj
./install.sh --shortcut   # instaliraj + veži Super+Space (Cinnamon)
```

Instalira se u `~/.local` — bez root prava:

```
~/.local/bin/aura-launcher
~/.local/share/aura-launcher/
~/.local/share/applications/org.aura.Launcher.desktop
~/.local/share/icons/hicolor/scalable/apps/org.aura.Launcher.svg
```

Uklanjanje:

```bash
./uninstall.sh
```

## Pokretanje

```bash
aura-launcher          # otvori launcher
aura-launcher --quit   # zaustavi pozadinsku instancu
aura-launcher --version
```

Aplikacija radi kao **jedna instanca** — ako je već pokrenuta u pozadini,
novi poziv samo prikaže prozor (trenutno otvaranje).

### Prečica na tastaturi (Cinnamon)

`System Settings → Keyboard → Shortcuts → Custom Shortcuts`

| Polje | Vrednost |
|---|---|
| Name | Aura Launcher |
| Command | `aura-launcher` |
| Keybind | `Super+Space` |

GNOME: `Settings → Keyboard → Custom Shortcuts → +`, isti podaci.

## Kako se koristi

```
fire                    → pronađi Firefox
2*3+4                   → 10 (Enter kopira rezultat)
g python gtk4 tutorial  → Google pretraga
yt lo-fi beats          → YouTube pretraga
github.com              → otvori sajt
reboot                  → restart računara
```

## Teme

Launcher prati sistemsko podešavanje i menja se **u hodu** — dovoljno je da
promeniš temu u sistemu i prozor se prefarba bez restarta.

Kako se otkriva tema:

| Izvor | Desktop |
|---|---|
| `color-scheme` ključ | GNOME 42+, KDE, XFCE 4.18+ |
| Naziv teme (`*dark*`) | Cinnamon, MATE |
| `Adw.StyleManager` | libadwaita |
| `gtk-application-prefer-dark-theme` | rezerva |

Ručno forsiranje teme (korisno za testiranje):

```bash
AURA_THEME=dark aura-launcher
AURA_THEME=light aura-launcher
```

## Struktura projekta

```
aura_launcher/
├── app.py            # Gtk.Application, komandna linija
├── window.py         # glavni prozor i UI logika
├── app_indexer.py    # indeksiranje .desktop fajlova + rangiranje
├── calculator.py     # bezbedno izračunavanje izraza
├── web_search.py     # veb pretrage i URL detekcija
├── system_actions.py # lock / reboot / shutdown / logout
├── theme.py          # detekcija dark/light + praćenje promena
├── style.css         # raspored i struktura
├── theme-dark.css    # tamna paleta
└── theme-light.css   # svetla paleta
```

## Prilagođavanje

**Boje** — `aura_launcher/theme-dark.css` i `theme-light.css`.
Svaka tema je lista `@define-color` vrednosti; `style.css` ih samo koristi.
Akcenat je gradijent `#7c5cff → #22d3ee` na ikonici kalkulatora.

**Nove veb pretrage** — `aura_launcher/web_search.py`, rečnik `PROVIDERS`:

```python
"so": {"name": "Stack Overflow",
       "url": "https://stackoverflow.com/search?q={}",
       "icon": "utilities-terminal-symbolic"},
```

**Nove sistemske akcije** — `aura_launcher/system_actions.py`, lista `ACTIONS`.

**Broj vidljivih rezultata** — `MAX_LIST_HEIGHT` u `aura_launcher/window.py`.

## Razvoj

```bash
python3 tools/test_logic.py        # testovi logike (bez displeja)
python3 tools/smoke_test.py        # gradi prozor i proverava pretrage
python3 tools/screenshot.py "" docs/preview.png
python3 tools/make_demo_gif.py     # regeneriše docs/demo.gif
```

CI (GitHub Actions) pokreće testove logike, gradi prozor pod Xvfb-om i
proverava sintaksu shell skripti.

## Licenca

MIT
