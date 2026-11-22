import pygame
import chess
import sys
import random
from agent import RandomAgent

# ================= CONFIG =================
WIDTH, HEIGHT = 600, 700
SQ_SIZE = WIDTH // 8
FPS = 30
WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
SELECT_COLOR = (255, 0, 0)
BLAST_COLOR = (255, 69, 0)
BG_COLOR = (255, 255, 255)

PIECES = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
}

class ChessMinesweeper:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # Initialize sound
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess × Minesweeper: Audio Edition")
        self.clock = pygame.time.Clock()

        # Load Fonts
        self.font = pygame.font.SysFont("segoe ui symbol", 48)
        self.ui_font = pygame.font.SysFont("arial", 22)

        # Load Sound
        try:
            self.explosion_sound = pygame.mixer.Sound("explosion.wav")
        except:
            self.explosion_sound = None
            print("Note: 'explosion.wav' not found. Playing without sound.")

        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves = []
        self.game_over = False
        self.message = "Mines activate after 16 moves."

        self.mines = set()
        self.adjacent_cache = {}
        self.move_count = 0
        self.mines_active = False
        self.blast_square = None

        self.king_lives = { chess.WHITE: 3, chess.BLACK: 3 }
        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK
        self.agent = RandomAgent(self.ai_color)

    def respawn_king(self, color):
        back_rank = chess.E1 if color == chess.WHITE else chess.E8
        if self.board.piece_at(back_rank) is None:
            self.board.set_piece_at(back_rank, chess.Piece(chess.KING, color))
        else:
            ranks = chess.SquareSet(chess.BB_RANK_1 if color == chess.WHITE else chess.BB_RANK_8)
            for sq in ranks:
                if self.board.piece_at(sq) is None:
                    self.board.set_piece_at(sq, chess.Piece(chess.KING, color))
                    break

    def place_mines(self):
        empty = [sq for sq in chess.SQUARES if self.board.piece_at(sq) is None]
        self.mines = set(random.sample(empty, min(12, len(empty))))
        self.build_adjacent_cache()

    def build_adjacent_cache(self):
        self.adjacent_cache = {sq: 0 for sq in chess.SQUARES}
        for sq in self.mines:
            f, r = chess.square_file(sq), chess.square_rank(sq)
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0: continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        self.adjacent_cache[chess.square(nf, nr)] += 1

    def apply_move(self, move):
        piece = self.board.piece_at(move.from_square)
        if not piece: return

        color = piece.color
        is_king = piece.piece_type == chess.KING

        self.board.push(move)
        self.move_count += 1

        if self.mines_active and move.to_square in self.mines:
            # --- START EXPLOSION SEQUENCE ---
            self.blast_square = move.to_square
            if self.explosion_sound:
                self.explosion_sound.play()

            self.mines.remove(move.to_square)
            self.board.remove_piece_at(move.to_square)

            if is_king:
                self.king_lives[color] -= 1
                self.message = f"💥 KING HIT! Lives: {self.king_lives[color]}"
                if self.king_lives[color] <= 0:
                    self.game_over = True
            else:
                self.message = "💣 PIECE DESTROYED!"

            # Render blast, wait for player to process
            self.draw_board()
            pygame.display.flip()
            pygame.time.delay(1000)

            if is_king and not self.game_over:
                self.respawn_king(color)

            self.blast_square = None
            # --- END EXPLOSION SEQUENCE ---
        else:
            self.message = f"{'White' if self.board.turn == chess.WHITE else 'Black'}'s turn"

        if self.move_count == 16:
            self.mines_active = True
            self.place_mines()
            self.message = "⚠️ MINES ACTIVATED!"

    def handle_click(self, pos):
        if self.game_over or self.board.turn != self.human_color:
            return
        c, r = pos[0] // SQ_SIZE, pos[1] // SQ_SIZE
        if c > 7 or r > 7: return
        square = chess.square(c, 7 - r)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.human_color:
                self.selected_square = square
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
        else:
            move = next((m for m in self.legal_moves if m.to_square == square), None)
            if move:
                self.apply_move(move)
            self.selected_square = None
            self.legal_moves = []

    def draw_board(self):
        self.screen.fill(BG_COLOR)
        for sq in chess.SQUARES:
            c, r = chess.square_file(sq), 7 - chess.square_rank(sq)
            color = WHITE_COLOR if (chess.square_file(sq) + chess.square_rank(sq)) % 2 != 0 else BLACK_COLOR
            pygame.draw.rect(self.screen, color, (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

            # Draw Blast UI
            if self.blast_square == sq:
                center = (c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2)
                pygame.draw.circle(self.screen, (255, 255, 0), center, SQ_SIZE // 2) # Inner yellow
                pygame.draw.circle(self.screen, BLAST_COLOR, center, SQ_SIZE // 3)   # Outer orange

            if self.selected_square == sq:
                pygame.draw.rect(self.screen, SELECT_COLOR, (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)

            if any(m.to_square == sq for m in self.legal_moves):
                center = (c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2)
                pygame.draw.circle(self.screen, (0, 255, 0), center, 6)

            # Proximity hints
            if self.mines_active and self.board.piece_at(sq):
                val = self.adjacent_cache.get(sq, 0)
                if val > 0:
                    hint = self.ui_font.render(str(val), True, (200, 0, 0))
                    self.screen.blit(hint, (c * SQ_SIZE + 5, r * SQ_SIZE + 5))

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                symbol = PIECES[piece.symbol()]
                text = self.font.render(symbol, True, (0, 0, 0))
                c, r = chess.square_file(sq), 7 - chess.square_rank(sq)
                rect = text.get_rect(center=(c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2))
                self.screen.blit(text, rect)

        # UI Stats
        self.screen.blit(self.ui_font.render(self.message, True, (0, 0, 0)), (20, 610))
        self.screen.blit(self.ui_font.render(f"W Lives: {self.king_lives[chess.WHITE]} | B Lives: {self.king_lives[chess.BLACK]}", True, (0, 0, 0)), (20, 640))
        self.screen.blit(self.ui_font.render(f"Move Count: {self.move_count}/16", True, (100, 100, 100)), (20, 670))

    def run(self):
        while True:
            self.draw_board()
            pygame.display.flip()

            if not self.game_over and self.board.turn == self.ai_color:
                pygame.time.delay(500)
                move = self.agent.get_move(self.board, self.mines, self.adjacent_cache)
                if move:
                    self.apply_move(move)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            self.clock.tick(FPS)

if __name__ == "__main__":
    ChessMinesweeper().run()
