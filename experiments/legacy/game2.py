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
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess × Minesweeper: Weight Fix Edition")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("segoe ui symbol", 48)
        self.ui_font = pygame.font.SysFont("arial", 22)

        try:
            self.explosion_sound = pygame.mixer.Sound("explosion.wav")
        except:
            self.explosion_sound = None

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

    def build_adjacent_cache(self):
        """Calculates Minesweeper weights for EVERY square based on current mine positions."""
        self.adjacent_cache = {sq: 0 for sq in chess.SQUARES}
        for mine_sq in self.mines:
            f, r = chess.square_file(mine_sq), chess.square_rank(mine_sq)
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0: continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        target_sq = chess.square(nf, nr)
                        self.adjacent_cache[target_sq] += 1

    def place_mines(self):
        """Initial placement of exactly 4 mines."""
        empty = [sq for sq in chess.SQUARES if self.board.piece_at(sq) is None]
        self.mines = set(random.sample(empty, min(4, len(empty))))
        self.build_adjacent_cache()

    def relocate_mine(self, hit_sq):
        """Removes mine from hit square and forces it to a new location."""
        if hit_sq in self.mines:
            self.mines.remove(hit_sq)

            # Find squares that are empty of pieces AND don't have a mine already
            valid_squares = [sq for sq in chess.SQUARES if self.board.piece_at(sq) is None and sq not in self.mines]

            if valid_squares:
                new_sq = random.choice(valid_squares)
                self.mines.add(new_sq)

            # CRITICAL: Rebuild weights immediately after the mine moves
            self.build_adjacent_cache()

    def apply_move(self, move):
        piece = self.board.piece_at(move.from_square)
        if not piece: return

        color = piece.color
        is_king = piece.piece_type == chess.KING

        # 1. Execute the move
        self.board.push(move)
        self.move_count += 1

        # 2. Check for Mine Activation
        if self.mines_active and move.to_square in self.mines:
            self.blast_square = move.to_square
            if self.explosion_sound:
                self.explosion_sound.play()

            if is_king:
                # King loses life, mine relocates, king stays
                self.king_lives[color] -= 1
                self.relocate_mine(move.to_square)
                self.message = f"💥 KING HIT! {self.king_lives[color]} Left. Mine shifted!"
                if self.king_lives[color] <= 0:
                    self.game_over = True
            else:
                # Piece destroyed, mine relocates (keeping count at 4)
                self.relocate_mine(move.to_square)
                self.board.remove_piece_at(move.to_square)
                self.message = "💣 PIECE DESTROYED! Mine shifted!"

            # Force weight refresh after explosion logic
            self.build_adjacent_cache()

            # Render blast feedback
            self.draw_board()
            pygame.display.flip()
            pygame.time.delay(800)
            self.blast_square = None
        else:
            self.message = f"{'White' if self.board.turn == chess.WHITE else 'Black'}'s turn"

        # 3. Handle First-time Activation
        if self.move_count == 16 and not self.mines_active:
            self.mines_active = True
            self.place_mines()
            self.message = "⚠️ 4 MINES ACTIVATED!"

        # Ensure hints are updated even on safe moves
        if self.mines_active:
            self.build_adjacent_cache()

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

            if self.blast_square == sq:
                center = (c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2)
                pygame.draw.circle(self.screen, (255, 255, 0), center, SQ_SIZE // 2)
                pygame.draw.circle(self.screen, BLAST_COLOR, center, SQ_SIZE // 3)

            if self.selected_square == sq:
                pygame.draw.rect(self.screen, SELECT_COLOR, (c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)

            if any(m.to_square == sq for m in self.legal_moves):
                center = (c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2)
                pygame.draw.circle(self.screen, (0, 255, 0), center, 6)

            # Draw the Weights (Proximity numbers)
            if self.mines_active:
                piece = self.board.piece_at(sq)
                if piece:
                    val = self.adjacent_cache.get(sq, 0)
                    if val > 0:
                        # Draw number behind/beside piece
                        hint = self.ui_font.render(str(val), True, (220, 0, 0))
                        self.screen.blit(hint, (c * SQ_SIZE + 2, r * SQ_SIZE + 2))

        # Draw Pieces
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
        self.screen.blit(self.ui_font.render(f"W King: {self.king_lives[chess.WHITE]} | B King: {self.king_lives[chess.BLACK]}", True, (0, 0, 0)), (20, 640))
        self.screen.blit(self.ui_font.render(f"Active Mines: {len(self.mines)} | Move: {self.move_count}/16", True, (100, 100, 100)), (20, 670))

    def run(self):
        while True:
            self.draw_board()
            pygame.display.flip()

            if not self.game_over and self.board.turn == self.ai_color:
                pygame.time.delay(500)
                # Pass current state to agent
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
