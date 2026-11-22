# Chess Minesweeper

Chess Minesweeper is a desktop chess variant with hidden mines, proximity clues, and three lives per king. Play White against a computer opponent or share the board with another player.

## Install and play

Use CPython 3.10–3.13 and a graphical desktop. Run these commands from the project directory.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\chess-minesweeper.exe
```

**macOS and Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/chess-minesweeper
```

The examples below assume your virtual environment is active. You can also use the full executable path from the installation steps above.

```sh
chess-minesweeper --mode relocating --opponent local
chess-minesweeper --opponent random --seed 42
chess-minesweeper --sound /path/to/explosion.wav
chess-minesweeper --help
```

`python -m chess_minesweeper` is another entry point. From the checkout, `python game.py` and `python game2.py` launch the classic and relocating editions respectively after installation.

## How to play

- Click one of your pieces, then click a highlighted destination. Press `Q`, `R`, `B`, or `N` to choose a promotion piece.
- Mines activate after 16 plies (eight moves per side). The number on an occupied square counts hidden mines in its eight neighboring squares.
- A piece that lands on a mine is removed. A king loses one life. Castling checks both landing squares. Passing over a mine leaves it in place.
- Press `R` to restart or `Esc` to close. During promotion, `Esc` cancels the selection.

| Mode | Mines | King hit |
| --- | --- | --- |
| `classic` (default) | Starts with 12 mines. Each detonated mine is consumed. | The king returns to a safe, empty back-rank square, preferring its starting square. |
| `relocating` | Starts with four mines. A detonated mine moves to a different empty square when one is available. | The king stays where it landed. |

Checkmate and automatic chess draws end the game. A side also loses if its king runs out of lives, it has no safe square for a classic respawn, or a blast exposes its own king to check. Mine activation and blasts reset the repetition history and move clock for automatic draws.

The default `search` opponent uses a three-ply chess search with access to the actual mine positions for its immediate move. The `random` opponent selects uniformly from legal moves. Use `local` for two players at the same computer.

## Development and release

- [Contributing](CONTRIBUTING.md) covers the code layout and local checks.
- [Deployment](docs/deployment.md) covers building, testing, and distributing the package through GitHub.
- [Experiments](experiments/README.md) documents the original prototypes and model-training notebooks available in the source checkout.

The desktop package requires Pygame and python-chess. PyTorch and the research checkpoints are used by the training experiments.
