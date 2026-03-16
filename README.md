# FoodHelper - Matdagbok

En enkel matdagbok med bilder för selektiva ätare. Fotografera mat, betygsätt och skriv anteckningar om hur det kändes.

## Funktioner

- Fotografera/välj bilder på maträtter
- Betygsätt mat (från "Usch!" till "Älskar det!")
- Skriv anteckningar om känslor kring maten
- Se alla prövade maträtter i en lista

## Installation

```bash
# Kräver GTK4 och libadwaita
# Ubuntu/Debian:
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1

# Fedora:
sudo dnf install python3-gobject gtk4 libadwaita

# macOS (Homebrew):
brew install gtk4 libadwaita pygobject3

# Installera appen:
pip install .
```

## Körning

```bash
foodhelper
# eller:
python -m foodhelper.main
```

## Datalagring

All data sparas i `~/.local/share/foodhelper/`:
- `matdagbok.json` - matdagboken
- `photos/` - kopierade bilder
