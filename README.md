# Color War Game

This project contains two versions of a small territory control experiment written with **pygame**.
The original monolithic implementation lives in `src/ColorWarGame.py` while a
much lighter refactor can be launched via `src/colorwar/main.py`.

## Requirements

- Python 3.9+
- `pygame`
- `pygame_gui`

Install the requirements with:

```bash
pip install pygame pygame_gui
```

## Running `ColorWarGame.py`

The full feature demo is started directly from the `src` folder:

```bash
python src/ColorWarGame.py
```

A window will open with several GUI buttons along the bottom.
Use **Save** or **Load** to manage games, **New Game** to reset, and **Quit** or
press `Esc`/`Q` to exit.

## Running the simplified version

```bash
python -m colorwar.main
```

This spawns a few random factions that automatically expand each frame.

## `.cwgsave` File Format

Save files are plain text. They begin with a `[GRID]` section where each line
represents a row of comma‑separated hex colors (or `None` for empty cells):

```
[GRID]
#f183f3,#f183f3,None,...
```

After the grid comes a `[FACTIONS]` section listing one faction per line:

```
[FACTIONS]
<color>|<name>|<behavior>|<tier>|<symbol>|<dna>|<capital>|<aggression>|<defense>|<expansionism>|<risk>
```

Values are separated by `|` characters. `capital` is stored as a Python tuple
representing the starting coordinate.

## The `saves/` Folder

Example `.cwgsave` files are stored in the `saves/` directory. You can load them
from the game or use the folder for your own save games.

## Basic Controls

- **Save**, **Load**, **New Game**, and **Quit** buttons appear at the bottom of
the window.
- Press `Esc` or `Q` at any time to close the game window.
