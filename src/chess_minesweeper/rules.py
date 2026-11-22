"""Game state and variant rules, independent of the desktop interface."""

import random
from dataclasses import dataclass
from enum import Enum

import chess

ACTIVATION_PLY = 16
STARTING_LIVES = 3


class MineMode(str, Enum):
    CLASSIC = "classic"
    RELOCATING = "relocating"


NEIGHBORS = {
    square: frozenset(chess.SquareSet(chess.BB_KING_ATTACKS[square])) for square in chess.SQUARES
}


def color_name(color: chess.Color) -> str:
    return "White" if color == chess.WHITE else "Black"


def chess_end_message(outcome: chess.Outcome | None) -> str | None:
    if outcome is None:
        return None
    reason = outcome.termination.name.replace("_", " ").lower()
    if outcome.winner is None:
        return f"Draw by {reason}."
    return f"{color_name(outcome.winner)} wins by {reason}."


def landing_squares(board: chess.Board, move: chess.Move) -> tuple[chess.Square, ...]:
    """Return the destination of each piece moved by a standard chess move."""
    if board.is_castling(move):
        rook_file = 5 if board.is_kingside_castling(move) else 3
        rook_square = chess.square(rook_file, chess.square_rank(move.to_square))
        return move.to_square, rook_square
    return (move.to_square,)


@dataclass(frozen=True)
class MoveResult:
    message: str
    blasts: tuple[chess.Square, ...] = ()


class Game:
    def __init__(
        self,
        mode: MineMode = MineMode.CLASSIC,
        *,
        seed: int | None = None,
        board: chess.Board | None = None,
    ) -> None:
        self.mode = MineMode(mode)
        self.board = chess.Board() if board is None else board.copy()
        self.rng = random.Random(seed)
        self.ply = self.board.ply()
        self.king_lives = {chess.WHITE: STARTING_LIVES, chess.BLACK: STARTING_LIVES}
        self.mines: set[chess.Square] = set()
        if self.mines_active:
            self._place_mines()
        self.end_message = chess_end_message(self.board.outcome())

    @property
    def mines_active(self) -> bool:
        return self.ply >= ACTIVATION_PLY

    def hint(self, square: chess.Square) -> int:
        return len(NEIGHBORS[square] & self.mines)

    def _empty_squares(self, excluded: set[chess.Square]) -> list[chess.Square]:
        return [
            square
            for square in chess.SQUARES
            if square not in excluded and self.board.piece_at(square) is None
        ]

    def _place_mines(self) -> None:
        count = 12 if self.mode == MineMode.CLASSIC else 4
        empty = self._empty_squares(set())
        self.mines = set(self.rng.sample(empty, min(count, len(empty))))

    def _respawn_king(self, color: chess.Color) -> bool:
        rank = 0 if color == chess.WHITE else 7
        for file in (4, 0, 1, 2, 3, 5, 6, 7):
            square = chess.square(file, rank)
            if (
                square not in self.mines
                and self.board.piece_at(square) is None
                and not self.board.is_attacked_by(not color, square)
            ):
                self.board.set_piece_at(square, chess.Piece(chess.KING, color))
                return True
        return False

    def play(self, move: chess.Move) -> MoveResult:
        if self.end_message is not None or not self.board.is_legal(move):
            raise ValueError(f"Cannot play {move.uci()} in this position.")

        color = self.board.turn
        blasts = tuple(
            square for square in landing_squares(self.board, move) if square in self.mines
        )
        self.board.push(move)
        self.ply += 1
        message = ""

        if blasts:
            message = self._resolve_blasts(blasts, color)
        if self.ply == ACTIVATION_PLY:
            self._place_mines()
            self.board.clear_stack()
            self.board.halfmove_clock = 0
            message = f"{len(self.mines)} hidden mines are now active."
        if self.end_message is None:
            self.end_message = chess_end_message(self.board.outcome())
        return MoveResult(self.end_message or message, blasts)

    def _resolve_blasts(self, blasts: tuple[chess.Square, ...], color: chess.Color) -> str:
        hit_king = self.board.king(color) in blasts
        destroyed = False
        for square in blasts:
            self.mines.remove(square)
            if square == self.board.king(color):
                self.king_lives[color] -= 1
                if self.mode == MineMode.CLASSIC:
                    self.board.remove_piece_at(square)
            else:
                self.board.remove_piece_at(square)
                destroyed = True

        if self.mode == MineMode.RELOCATING:
            open_squares = self._empty_squares(self.mines.union(blasts))
            self.mines.update(self.rng.sample(open_squares, min(len(blasts), len(open_squares))))

        # Changes to the board, lives, or mine positions end the repetition history.
        self.board.clear_stack()
        self.board.halfmove_clock = 0
        self.board.ep_square = None
        winner = color_name(not color)
        if self.king_lives[color] == 0:
            self.end_message = f"{winner} wins. {color_name(color)}'s king ran out of lives."
        elif hit_king and self.mode == MineMode.CLASSIC and not self._respawn_king(color):
            self.end_message = f"{winner} wins. No safe square for the king to return."
        elif self.board.is_attacked_by(not color, self.board.king(color)):
            self.end_message = f"{winner} wins. A blast exposed {color_name(color)}'s king."

        messages = []
        if hit_king:
            messages.append(f"{color_name(color)} king hit. Lives left: {self.king_lives[color]}.")
        if destroyed:
            messages.append("A piece was destroyed.")
        return " ".join(messages)
