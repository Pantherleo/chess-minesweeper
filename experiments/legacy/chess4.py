import pygame
import chess
import random
import sys

# ================= CONFIG =================
WIDTH, HEIGHT = 600, 700
SQ_SIZE = WIDTH // 8
FPS = 30

WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
SELECT_COLOR = (255, 0, 0)
TEXT_COLOR = (0, 0, 0)
BG_COLOR = (255, 255, 255)

NUMBER_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}

PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
}


class ChessMinesweeper:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess × Minesweeper")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(None, 48)
        self.num_font = pygame.font.SysFont(None, 18, bold=True)
        self.ui_font = pygame.font.SysFont(None, 22)

        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves = []

        self.move_count = 0
        self.king_lives = 3
        self.mines = set()
        self.adjacent_cache = {}
        self.mines_active = False
        self.game_over = False
        self.message = ""

        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK
        self.waiting_for_ai = False

    # ================= MINES =================
    def get_empty_squares(self):
        return [sq for sq in chess.SQUARES if self.board.piece_at(sq) is None]

    def place_mines(self):
        empty = self.get_empty_squares()
        self.mines = set(random.sample(empty, min(4, len(empty))))
        self.build_adjacent_cache()

    def build_adjacent_cache(self):
        self.adjacent_cache.clear()
        for sq in chess.SQUARES:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            count = 0
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        if chess.square(nf, nr) in self.mines:
                            count += 1
            self.adjacent_cache[sq] = count

    # ================= AI =================
    def ai_move(self):
        moves = list(self.board.legal_moves)
        if moves:
            self.make_move(random.choice(moves))

    # ================= GAME LOGIC =================
    def make_move(self, move):
        piece = self.board.piece_at(move.from_square)
        is_king = piece and piece.piece_type == chess.KING

        self.board.push(move)
        self.move_count += 1
        self.message = ""

        if self.mines_active and move.to_square in self.mines:
            self.mines.remove(move.to_square)
            self.board.remove_piece_at(move.to_square)
            self.build_adjacent_cache()

            if is_king:
                self.king_lives -= 1
                self.message = "💥 King hit a mine!"
                if self.king_lives <= 0:
                    self.game_over = True
                    self.message = "☠️ Game Over"
            else:
                self.message = "💣 Piece destroyed!"

        if self.move_count == 16:
            self.mines_active = True
            self.place_mines()
            self.message = "⚠️ Mines Activated!"

        elif self.mines_active and (self.move_count - 16) % 10 == 0:
            self.place_mines()
            self.message = "🔄 Mines Relocated"

        if self.board.is_checkmate():
            self.game_over = True
            self.message = "♚ Checkmate!"

        if not self.game_over and self.board.turn == self.ai_color:
            self.waiting_for_ai = True

    # ================= INPUT =================
    def handle_click(self, pos):
        if self.game_over or self.board.turn != self.human_color:
            return

        col, row = pos[0] // SQ_SIZE, pos[1] // SQ_SIZE
        if col > 7 or row > 7:
            return

        square = chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves = [
                    m for m in self.board.legal_moves if m.from_square == square
                ]
        else:
            promotion = None
            piece = self.board.piece_at(self.selected_square)

            if piece and piece.piece_type == chess.PAWN:
                if chess.square_rank(square) in (0, 7):
                    promotion = chess.QUEEN

            move = chess.Move(self.selected_square, square, promotion=promotion)

            if move in self.legal_moves:
                self.make_move(move)

            self.selected_square = None
            self.legal_moves = []

    # ================= DRAW =================
    def draw_board(self):
        self.screen.fill(BG_COLOR)

        for r in range(8):
            for c in range(8):
                color = WHITE_COLOR if (r + c) % 2 == 0 else BLACK_COLOR
                pygame.draw.rect(
                    self.screen, color,
                    (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )

                sq = chess.square(c, 7 - r)
                if self.mines_active:
                    count = self.adjacent_cache.get(sq, 0)
                    if count > 0:
                        num = self.num_font.render(str(count), True, NUMBER_COLORS[count])
                        self.screen.blit(num, (c * SQ_SIZE + 4, r * SQ_SIZE + 4))

        if self.selected_square is not None:
            c = chess.square_file(self.selected_square)
            r = 7 - chess.square_rank(self.selected_square)
            pygame.draw.rect(
                self.screen, SELECT_COLOR,
                (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 3
            )

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                symbol = PIECES[piece.symbol()]
                text = self.font.render(symbol, True, (0, 0, 0))
                c = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
                rect = text.get_rect(center=(
                    c * SQ_SIZE + SQ_SIZE // 2,
                    r * SQ_SIZE + SQ_SIZE // 2
                ))
                self.screen.blit(text, rect)

        self.screen.blit(
            self.ui_font.render(self.message, True, (200, 0, 0)), (20, 610)
        )

    # ================= LOOP =================
    def run(self):
        while True:
            self.draw_board()
            pygame.display.flip()

            if self.waiting_for_ai:
                pygame.time.delay(300)
                self.ai_move()
                self.waiting_for_ai = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.clock.tick(FPS)


if __name__ == "__main__":
    ChessMinesweeper().run()
