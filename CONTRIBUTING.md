# Contributing

Use a virtual environment with CPython 3.10–3.13. Create one using the [installation steps](README.md#install-and-play), then activate it with `source .venv/bin/activate` in a POSIX shell or `.\.venv\Scripts\Activate.ps1` in PowerShell. Install the editable package with its development tools.

```sh
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
```

Run the desktop app with `python -m chess_minesweeper`. Use `--seed 42` when reporting a reproducible mine layout or computer response. Include the mode, opponent, operating system, Python version, and move sequence when reporting a gameplay problem.

## Code layout

| Path | Purpose |
| --- | --- |
| `src/chess_minesweeper/cli.py` | Parses command-line arguments and starts Pygame. |
| `src/chess_minesweeper/desktop.py` | Draws the board, handles input, and schedules the computer turn. |
| `src/chess_minesweeper/rules.py` | Validates moves and manages mines, king lives, and outcomes. |
| `src/chess_minesweeper/agents.py` | Selects computer moves on a snapshot of the board. |
| `tests/` | Covers game rules, opponents, and input with a headless display. |
| `experiments/` | Keeps historical prototypes and research in the source checkout. |

Keep state transitions in `Game.play` so they can be tested without a display. Add a regression test when changing a rule or a gameplay case the suite does not already cover. Run `python -m ruff format .` when updating Python formatting.
