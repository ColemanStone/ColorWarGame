# Color War Game

This repository contains a small pygame experiment that simulates colored factions vying for territory on a grid. The original code bundled many features into a single large file. A lightweight version has been added under `src/colorwar`.

## Requirements

- Python 3.9+
- `pygame` (`pip install pygame`)

## Running the simplified version

```bash
python -m colorwar.main
```

This will open a window and spawn a few random factions that expand each frame.

## Legacy Code

The original experimental implementation lives in `src/ColorWarGame.py` and is retained for reference but it is quite large and unstructured.

## Running Tests

Install the development requirements:

```bash
pip install -r requirements-dev.txt
```

Then execute the test suite with:

```bash
pytest
```
