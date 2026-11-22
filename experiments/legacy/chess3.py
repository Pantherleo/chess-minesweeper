import pygame
import chess
import random
import sys
import os

# ================= CONFIG =================
WIDTH, HEIGHT = 600, 700
SQ_SIZE = WIDTH // 8
FPS = 30

WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
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

ASSET_DIR = "assets/pieces"

PIECE_MAP = {
    'P': 'wp', 'R': 'wr', 'N': 'wn', 'B': 'wb', 'Q': 'wq', 'K': 'wk',
    'p': 'bp', 'r': 'br', 'n': 'bn', 'b': 'bb', 'q': 'bq', 'k': 'bk'
}


# ================= GAME =================
class ChessMinesweeper:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess × Minesweeper (vs Computer)")
        self.clock = pygame.time.Clock()

        self.num_font = pygame.font.SysFont(None, 18, bold=True)
        self.ui_font = pygame.font.SysFont(None, 22)

        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves = []

        # ---- GAME STATE ----
        self.move_count = 0
        self.king_lives = 3
        self.mines = set()
        self.adjacent_cache = {}
        self.mines_active = False
        self.game_over = False
        self.message = ""

        # ---- AI CONFIG ----
        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK

        self.load_piece_images()

    # ================= ASSETS =================
    def load_piece_images(self):
        self.piece_images = {}
        for key, name in PIECE_MAP.items():
            path = os.path.join(ASSET_DIR, f"{name}.png")
            img = pygame.image.load(path).convert_alpha()
            self.piece_images[key] = pygame.transform.smoothscale(
                img, (SQ_SIZE, SQ_SIZE)
            )

    # ================= MINES =================
    def get_empty_squares(self):
        return [sq for sq in chess.SQUARES if self.board.piece_at(sq) is None]

    def place_mines(self):
        empty = self.get_empty_squares()
        self.mines = set(random.sample(empty, min(4, len(empty))))
        self.build_adjacent_cache()

    def build_adjacent_cache(self):
        self.adjacent_cache = {sq: 0 for sq in chess.SQUARES}
        for sq in self.mines:
            f, r = chess.square_file(sq), chess.square_rank(sq)
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        self.adjacent_cache[chess.square(nf, nr)] += 1

    # ================= AI =================
    def ai_move(self):
        if self.game_over:
            return

        moves = list(self.board.legal_moves)
        if not moves:
            return

        move = random.choice(moves)
        pygame.time.delay(300)  # feels human
        self.make_move(move)

    # ================= GAME LOGIC =================
    def make_move(self, move):
        piece = self.board.piece_at(move.from_square)
        is_king = piece and piece.piece_type == chess.KING

        self.board.push(move)
        self.move_count += 1
        self.message = ""

        # ---- MINE HIT ----
        if self.mines_active and move.to_square in self.mines:
            self.mines.remove(move.to_square)
            self.board.remove_piece_at(move.to_square)
            self.build_adjacent_cache()

            if is_king:
                self.king_lives -= 1
                self.message = "💥 King hit a mine!"
                if self.king_lives <= 0:
                    self.game_over = True
                    self.message = "☠️ King lost all lives! Game Over"
            else:
                self.message = "💣 Piece destroyed!"

        # ---- MINE ACTIVATION ----
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

    # ================= INPUT =================
    def handle_click(self, pos):
        if self.game_over:
            return

        # Only allow human to play on their turn
        if self.board.turn != self.human_color:
            return

        col, row = pos[0] // SQ_SIZE, pos[1] // SQ_SIZE
        if col > 7 or row > 7:
            return

        square = chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.human_color:
                self.selected_square = square
                self.legal_moves = [
                    m for m in self.board.legal_moves if m.from_square == square
                ]
        else:
            move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            if move in self.legal_moves:
                self.make_move(move)

                # ---- AI RESPONDS ----
                if not self.game_over and self.board.turn == self.ai_color:
                    self.ai_move()

            self.selected_square = None
            self.legal_moves = []

    # ================= DRAW =================
    def draw_board(self):
        self.screen.fill(BG_COLOR)

        for r in range(8):
            for c in range(8):
                color = WHITE_COLOR if (r + c) % 2 == 0 else BLACK_COLOR
                pygame.draw.rect(self.screen, color,
                                 (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

                sq = chess.square(c, 7 - r)
                if self.mines_active:
                    count = self.adjacent_cache.get(sq, 0)
                    if count > 0:
                        num = self.num_font.render(str(count), True, NUMBER_COLORS[count])
                        self.screen.blit(num, (c*SQ_SIZE + 4, r*SQ_SIZE + 4))

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                img = self.piece_images[piece.symbol()]
                c = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
                self.screen.blit(img, (c*SQ_SIZE, r*SQ_SIZE))

        ui_y = 610
        status = f"Moves: {self.move_count} | King Lives: {self.king_lives}"
        self.screen.blit(self.ui_font.render(status, True, TEXT_COLOR), (20, ui_y))
        self.screen.blit(self.ui_font.render(self.message, True, (200, 0, 0)), (20, ui_y + 30))

    # ================= LOOP =================
    def run(self):
        while True:
            self.draw_board()
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(e.pos)

            self.clock.tick(FPS)


# ================= MAIN =================
if __name__ == "__main__":
    ChessMinesweeper().run()
