"""Compatibility launcher for the relocating-mine desktop edition."""

from chess_minesweeper.cli import main
from chess_minesweeper.rules import MineMode

if __name__ == "__main__":
    raise SystemExit(main(default_mode=MineMode.RELOCATING))
