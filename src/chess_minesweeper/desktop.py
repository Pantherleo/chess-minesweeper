"""Pygame display and input for Chess Minesweeper."""

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import chess
import pygame

from .agents import Agent, RandomAgent, SearchAgent
from .rules import ACTIVATION_PLY, Game, MineMode, color_name

BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8
WINDOW_SIZE = (BOARD_SIZE, BOARD_SIZE + 120)
AI_DELAY_MS = 350
BLAST_DURATION_MS = 800
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
PANEL = (30, 36, 33)
TEXT = (245, 241, 232)
SUBTEXT = (186, 199, 190)
AGENTS = {"search": SearchAgent, "random": RandomAgent, "local": None}

PROMOTION_KEYS = {
    pygame.K_q: chess.QUEEN,
    pygame.K_r: chess.ROOK,
    pygame.K_b: chess.BISHOP,
    pygame.K_n: chess.KNIGHT,
}


def square_at(position: tuple[int, int]) -> chess.Square | None:
    x, y = position
    if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
        return chess.square(x // SQUARE_SIZE, 7 - y // SQUARE_SIZE)
    return None


def square_rect(square: chess.Square) -> pygame.Rect:
    return pygame.Rect(
        chess.square_file(square) * SQUARE_SIZE,
        (7 - chess.square_rank(square)) * SQUARE_SIZE,
        SQUARE_SIZE,
        SQUARE_SIZE,
    )


class DesktopGame:
    def __init__(
        self,
        mode: MineMode,
        opponent: str,
        seed: int | None,
        sound_path: Path | None,
    ) -> None:
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Chess Minesweeper")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 21)
        self.hint_labels = {
            count: self.small_font.render(str(count), True, TEXT) for count in range(1, 9)
        }
        self.pieces = self._make_piece_surfaces()
        self.explosion_sound = self._load_sound(sound_path)
        self.mode = mode
        self.opponent = opponent
        self.seed = seed
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="chess-search")
        self.ai_move: Future[chess.Move | None] | None = None
        self.reset()

    @staticmethod
    def _load_sound(path: Path | None) -> pygame.mixer.Sound | None:
        if path is None:
            return None
        try:
            pygame.mixer.init()
            return pygame.mixer.Sound(str(path))
        except (pygame.error, OSError) as error:
            logging.warning("Explosion sound unavailable (%s)", error)
            return None

    @staticmethod
    def _make_piece_surfaces() -> dict[str, pygame.Surface]:
        pieces = [chess.Piece(kind, color) for color in chess.COLORS for kind in chess.PIECE_TYPES]
        glyphs = "".join(piece.unicode_symbol() for piece in pieces)
        for name in ("Segoe UI Symbol", "DejaVu Sans", "Apple Symbols", "Noto Sans Symbols 2"):
            path = pygame.font.match_font(name)
            if path is None:
                continue
            font = pygame.font.Font(path, 56)
            if all(metric is not None for metric in font.metrics(glyphs)):
                return {
                    piece.symbol(): font.render(piece.unicode_symbol(), True, (25, 27, 23))
                    for piece in pieces
                }

        font = pygame.font.Font(None, 36)
        surfaces = {}
        for piece in pieces:
            surface = pygame.Surface((48, 48), pygame.SRCALPHA)
            fill, ink = (TEXT, PANEL) if piece.color == chess.WHITE else (PANEL, TEXT)
            pygame.draw.circle(surface, ink, (24, 24), 23)
            pygame.draw.circle(surface, fill, (24, 24), 21)
            label = font.render(piece.symbol().upper(), True, ink)
            surface.blit(label, label.get_rect(center=(24, 24)))
            surfaces[piece.symbol()] = surface
        return surfaces

    def reset(self) -> None:
        if self.ai_move is not None:
            self.ai_move.cancel()
        self.ai_move = None
        self.game = Game(self.mode, seed=self.seed)
        factory = AGENTS[self.opponent]
        self.agent: Agent | None = factory(self.seed) if factory is not None else None
        self.selected: chess.Square | None = None
        self.destinations: dict[chess.Square, list[chess.Move]] = {}
        self.promotion: list[chess.Move] = []
        self.blasts: tuple[chess.Square, ...] = ()
        self.blast_until = 0
        self.ai_after = 0
        self.notice = ""

    def _clear_selection(self) -> None:
        self.selected = None
        self.destinations.clear()
        self.promotion = []

    def _select(self, square: chess.Square) -> None:
        self._clear_selection()
        if self.game.board.color_at(square) != self.game.board.turn:
            return
        self.selected = square
        for move in self.game.board.legal_moves:
            if move.from_square == square:
                self.destinations.setdefault(move.to_square, []).append(move)

    def _play(self, move: chess.Move) -> None:
        result = self.game.play(move)
        self._clear_selection()
        self.notice = result.message
        self.blasts = result.blasts
        now = pygame.time.get_ticks()
        self.blast_until = now + BLAST_DURATION_MS if self.blasts else now
        self.ai_after = now + AI_DELAY_MS
        if self.blasts and self.explosion_sound is not None:
            self.explosion_sound.play()

    def _ai_turn(self) -> bool:
        return self.agent is not None and self.game.board.turn == chess.BLACK

    def _click(self, position: tuple[int, int]) -> None:
        if self.game.end_message or self._ai_turn() or self.blasts or self.promotion:
            return
        square = square_at(position)
        if square is None or square == self.selected:
            self._clear_selection()
        elif square in self.destinations:
            moves = self.destinations[square]
            if len(moves) > 1:
                self.promotion = moves
            else:
                self._play(moves[0])
        else:
            self._select(square)

    def _handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click(event.pos)
        if event.type == pygame.KEYDOWN:
            if self.promotion:
                if event.key == pygame.K_ESCAPE:
                    self._clear_selection()
                elif event.key in PROMOTION_KEYS:
                    kind = PROMOTION_KEYS[event.key]
                    self._play(next(move for move in self.promotion if move.promotion == kind))
            elif event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_r:
                self.reset()
        return True

    def _update(self) -> None:
        now = pygame.time.get_ticks()
        if now >= self.blast_until:
            self.blasts = ()
        if self.game.end_message or self.agent is None or not self._ai_turn():
            return
        if self.ai_move is None:
            self.ai_move = self.worker.submit(
                self.agent.choose_move,
                self.game.board.copy(),
                frozenset(self.game.mines),
                self.game.king_lives[chess.BLACK],
            )
        if self.ai_move.done() and not self.blasts and now >= self.ai_after:
            move = self.ai_move.result()
            self.ai_move = None
            if move is None:
                raise RuntimeError("The computer found no move in an ongoing game.")
            self._play(move)

    def _draw_board(self) -> None:
        for square in chess.SQUARES:
            rect = square_rect(square)
            file, rank = chess.square_file(square), chess.square_rank(square)
            color = LIGHT_SQUARE if (file + rank) % 2 else DARK_SQUARE
            pygame.draw.rect(self.screen, color, rect)
            if square == self.selected:
                pygame.draw.rect(self.screen, (35, 90, 67), rect, 4)
            if square in self.destinations:
                pygame.draw.circle(self.screen, (48, 110, 76), rect.center, 9)
            if square in self.blasts:
                pygame.draw.circle(self.screen, (252, 163, 59), rect.center, 36)
                pygame.draw.circle(self.screen, (250, 221, 96), rect.center, 24)

            piece = self.game.board.piece_at(square)
            if piece is not None:
                surface = self.pieces[piece.symbol()]
                self.screen.blit(surface, surface.get_rect(center=rect.center))
                hint = self.game.hint(square)
                if hint:
                    center = (rect.x + 13, rect.y + 13)
                    pygame.draw.circle(self.screen, (128, 44, 28), center, 10)
                    label = self.hint_labels[hint]
                    self.screen.blit(label, label.get_rect(center=center))

    def _draw_status(self) -> None:
        self.screen.fill(PANEL, (0, BOARD_SIZE, BOARD_SIZE, WINDOW_SIZE[1] - BOARD_SIZE))
        turn = color_name(self.game.board.turn)
        if self.game.end_message:
            status = self.game.end_message
        elif self.promotion:
            status = "Promote to queen (Q), rook (R), bishop (B), or knight (N)."
        else:
            status = f"{turn} to move" if not self._ai_turn() else "Black is thinking..."
            if self.game.board.is_check():
                status += " - check"

        white, black = self.game.king_lives[chess.WHITE], self.game.king_lives[chess.BLACK]
        mine_status = (
            f"Mines remaining: {len(self.game.mines)}"
            if self.game.mines_active
            else f"Mines activate after {ACTIVATION_PLY - self.game.ply} more plies"
        )
        stats = f"King lives  W {white} / B {black}   |   {mine_status}   |   Ply {self.game.ply}"
        controls = "Esc cancel promotion" if self.promotion else "R restart   |   Esc close"
        notice = self.notice if self.notice != self.game.end_message else ""
        for offset, message, font, color in (
            (12, status, self.font, TEXT),
            (39, stats, self.small_font, SUBTEXT),
            (62, notice, self.small_font, TEXT),
            (88, controls, self.small_font, SUBTEXT),
        ):
            self.screen.blit(font.render(message, True, color), (16, BOARD_SIZE + offset))

    def run(self, *, smoke_test: bool = False) -> None:
        try:
            while True:
                for event in pygame.event.get():
                    if not self._handle_event(event):
                        return
                self._update()
                self._draw_board()
                self._draw_status()
                pygame.display.flip()
                if smoke_test:
                    break
                self.clock.tick(30)
        finally:
            self.worker.shutdown(wait=False, cancel_futures=True)
