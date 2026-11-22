"""Computer opponents for the desktop game."""

import random
from math import inf
from typing import Protocol

import chess

from .piece_values import MATERIAL, PIECE_SQUARES
from .rules import landing_squares

MATE_SCORE = 100_000


class Agent(Protocol):
    def choose_move(
        self, board: chess.Board, mines: frozenset[chess.Square], king_lives: int
    ) -> chess.Move | None: ...


class RandomAgent:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def choose_move(
        self, board: chess.Board, mines: frozenset[chess.Square], king_lives: int
    ) -> chess.Move | None:
        moves = list(board.legal_moves)
        return self.rng.choice(moves) if moves else None


class SearchAgent:
    """Search standard chess positions and penalize known mine landings."""

    def __init__(self, seed: int | None = None, depth: int = 3) -> None:
        if depth < 1:
            raise ValueError("Search depth must be at least one ply.")
        self.rng = random.Random(seed)
        self.depth = depth

    def choose_move(
        self, board: chess.Board, mines: frozenset[chess.Square], king_lives: int
    ) -> chess.Move | None:
        moves = list(board.legal_moves)
        self.rng.shuffle(moves)
        best_move = None
        best_score = -inf

        for move in moves:
            penalty = self._mine_penalty(board, move, mines, king_lives)
            if penalty == MATE_SCORE:
                score = -MATE_SCORE
            else:
                board.push(move)
                try:
                    score = -self._search(board, self.depth - 1, -inf, inf)
                finally:
                    board.pop()
                if penalty:
                    # A blast changes the position, so a standard-chess mate score is unreliable.
                    score = max(-5_000, min(score, 5_000)) - penalty
            if score > best_score:
                best_move, best_score = move, score
        return best_move

    @staticmethod
    def _mine_penalty(
        board: chess.Board,
        move: chess.Move,
        mines: frozenset[chess.Square],
        king_lives: int,
    ) -> int:
        destination, *rook_landing = landing_squares(board, move)
        penalty = MATERIAL[chess.ROOK] if mines.intersection(rook_landing) else 0
        if destination in mines:
            piece_type = board.piece_type_at(move.from_square)
            if piece_type == chess.KING:
                return MATE_SCORE if king_lives == 1 else penalty + 1_500
            penalty += MATERIAL[move.promotion or piece_type] + 200
        return penalty

    def _search(self, board: chess.Board, depth: int, alpha: float, beta: float) -> float:
        if board.is_insufficient_material() or board.is_seventyfive_moves():
            return 0
        moves = list(board.legal_moves)
        if not moves:
            return -(MATE_SCORE + depth) if board.is_check() else 0
        if depth == 0:
            return self._evaluate(board)

        best = -inf
        for move in sorted(moves, key=board.is_capture, reverse=True):
            board.push(move)
            try:
                score = -self._search(board, depth - 1, -beta, -alpha)
            finally:
                board.pop()
            best = max(best, score)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    @staticmethod
    def _evaluate(board: chess.Board) -> int:
        score = 0
        for square, piece in board.piece_map().items():
            # Tables run from a8 to h1, with White at the bottom.
            index = chess.square_mirror(square) if piece.color == chess.WHITE else square
            value = MATERIAL[piece.piece_type] + PIECE_SQUARES[piece.piece_type][index]
            score += value if piece.color == board.turn else -value
        return score
