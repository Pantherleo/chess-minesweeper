"""Command-line entry point for the desktop game."""

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from .rules import MineMode


def main(argv: Sequence[str] | None = None, *, default_mode: MineMode = MineMode.CLASSIC) -> int:
    parser = argparse.ArgumentParser(description="Play Chess Minesweeper on your desktop.")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in MineMode],
        default=default_mode.value,
        help="mine rules (default: %(default)s)",
    )
    parser.add_argument(
        "--opponent",
        choices=("search", "random", "local"),
        default="search",
        help="who plays Black, or local two-player (default: %(default)s)",
    )
    parser.add_argument("--seed", type=int, help="repeat mine placement and opponent choices")
    parser.add_argument("--sound", type=Path, metavar="FILE", help="optional explosion sound file")
    parser.add_argument("--smoke-test", action="store_true", help="render one frame and exit")
    args = parser.parse_args(argv)

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from .desktop import DesktopGame

    try:
        app = DesktopGame(MineMode(args.mode), args.opponent, args.seed, args.sound)
        app.run(smoke_test=args.smoke_test)
    except pygame.error as error:
        print(f"Chess Minesweeper could not run: {error}", file=sys.stderr)
        return 1
    finally:
        pygame.quit()
    return 0
