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


# ================= GAME =================
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
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            count = 0
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = file + df, rank + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        if chess.square(nf, nr) in self.mines:
                            count += 1
            self.adjacent_cache[sq] = count

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

            # REMOVE PIECE THAT HIT MINE
            self.board.remove_piece_at(move.to_square)

            self.build_adjacent_cache()

            if is_king:
                self.king_lives -= 1
                self.message = "💥 King hit a mine and died!"
                if self.king_lives <= 0:
                    self.game_over = True
                    self.message = "☠️ King lost all lives! Game Over"
            else:
                self.message = "💣 Piece hit a mine and died!"

        # ---- MINE ACTIVATION ----
        if self.move_count == 16:
            self.mines_active = True
            self.place_mines()
            self.message = "⚠️ Mines Activated!"

        elif self.mines_active and (self.move_count - 16) % 10 == 0:
            self.place_mines()
            self.message = "🔄 Mines Relocated"

        # ---- CHECKMATE ----
        if self.board.is_checkmate():
            self.game_over = True
            self.message = "♚ Checkmate!"

    # ================= INPUT =================
    def handle_click(self, pos):
        if self.game_over:
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
            move = chess.Move(self.selected_square, square)
            if move not in self.legal_moves:
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            if move in self.legal_moves:
                self.make_move(move)

            self.selected_square = None
            self.legal_moves = []

    # ================= DRAW =================
    def draw_board(self):
        self.screen.fill(BG_COLOR)

        for row in range(8):
            for col in range(8):
                color = WHITE_COLOR if (row + col) % 2 == 0 else BLACK_COLOR
                pygame.draw.rect(
                    self.screen, color,
                    (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )

                square = chess.square(col, 7 - row)

                if self.mines_active:
                    count = self.adjacent_cache.get(square, 0)
                    if count > 0:
                        num = self.num_font.render(
                            str(count), True, NUMBER_COLORS[count]
                        )
                        self.screen.blit(num, (col * SQ_SIZE + 4, row * SQ_SIZE + 4))

                if square == self.selected_square:
                    overlay = pygame.Surface((SQ_SIZE, SQ_SIZE))
                    overlay.set_alpha(120)
                    overlay.fill((0, 0, 255))
                    self.screen.blit(overlay, (col * SQ_SIZE, row * SQ_SIZE))

                if square in [m.to_square for m in self.legal_moves]:
                    pygame.draw.circle(
                        self.screen, (80, 80, 80),
                        (col * SQ_SIZE + SQ_SIZE // 2,
                         row * SQ_SIZE + SQ_SIZE // 2), 8
                    )

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                symbol = PIECES[piece.symbol()]
                color = (255, 255, 255) if piece.color else (0, 0, 0)
                text = self.font.render(symbol, True, color)

                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                rect = text.get_rect(center=(
                    col * SQ_SIZE + SQ_SIZE // 2,
                    row * SQ_SIZE + SQ_SIZE // 2
                ))
                self.screen.blit(text, rect)

        ui_y = 610
        status = f"Moves: {self.move_count} | King Lives: {self.king_lives}"
        if self.mines_active:
            status += " | 💣 MINES ACTIVE"

        self.screen.blit(self.ui_font.render(status, True, TEXT_COLOR), (20, ui_y))
        self.screen.blit(self.ui_font.render(self.message, True, (200, 0, 0)), (20, ui_y + 30))

        if self.game_over:
            over = self.ui_font.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(over, (250, ui_y + 15))

    # ================= LOOP =================
    def run(self):
        while True:
            self.draw_board()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.clock.tick(FPS)


# ================= MAIN =================
if __name__ == "__main__":
    ChessMinesweeper().run()
