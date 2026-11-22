import chess
import random

class SearchAgent:
    def __init__(self, color):
        self.color = color
        self.values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Piece-Square Tables (PST)
        # These are viewed from White's perspective.
        # For Black, we will flip the index during evaluation.
        self.pst = {
            chess.PAWN: [
                0,  0,  0,  0,  0,  0,  0,  0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5,  5, 10, 25, 25, 10,  5,  5,
                0,  0,  0, 20, 20,  0,  0,  0,
                5, -5,-10,  0,  0,-10, -5,  5,
                5, 10, 10,-20,-20, 10, 10,  5,
                0,  0,  0,  0,  0,  0,  0,  0
            ],
            chess.KNIGHT: [
                -50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50,
            ],
            chess.BISHOP: [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -20,-10,-10,-10,-10,-10,-10,-20,
            ],
            chess.ROOK: [
                0,  0,  0,  0,  0,  0,  0,  0,
                5, 10, 10, 10, 10, 10, 10,  5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                0,  0,  0,  5,  5,  0,  0,  0
            ],
            chess.QUEEN: [
                -20,-10,-10, -5, -5,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5,  5,  5,  5,  0,-10,
                -5,  0,  5,  5,  5,  5,  0, -5,
                0,  0,  5,  5,  5,  5,  0, -5,
                -10,  5,  5,  5,  5,  5,  0,-10,
                -10,  0,  5,  0,  0,  0,  0,-10,
                -20,-10,-10, -5, -5,-10,-10,-20
            ],
            chess.KING: [
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                20, 20,  0,  0,  0,  0, 20, 20,
                20, 30, 10,  0,  0, 10, 30, 20
            ]
        }

    def evaluate_board(self, board, mines):
        if board.is_checkmate():
            return 99999 if board.turn != self.color else -99999

        score = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece:
                # 1. Base Material Value
                val = self.values.get(piece.piece_type, 0)

                # 2. Positional Value (PST)
                # Flip the square index for black pieces so the table works for both sides
                pst_index = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
                val += self.pst.get(piece.piece_type, [0]*64)[pst_index]

                # 3. Minesweeper Penalty
                if sq in mines:
                    val -= 600 # Slightly increased penalty to prioritize survival

                if piece.color == self.color:
                    score += val
                else:
                    score -= val
        return score

    def minimax(self, board, depth, alpha, beta, is_maximizing, mines):
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board, mines)

        if is_maximizing:
            max_eval = -float('inf')
            # Move ordering: Captures first to optimize Alpha-Beta pruning
            moves = sorted(board.legal_moves, key=lambda m: board.is_capture(m), reverse=True)
            for move in moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False, mines)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            moves = sorted(board.legal_moves, key=lambda m: board.is_capture(m), reverse=True)
            for move in moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True, mines)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_move(self, board, mines, adjacent_cache):
        best_move = None
        best_value = -float('inf')
        depth = 3 # Can be bumped to 4 for 'Hard' mode

        moves = list(board.legal_moves)
        random.shuffle(moves)

        for move in moves:
            board.push(move)
            # Penalize moving into a mine immediately
            if move.to_square in mines:
                board_value = -1000
            else:
                board_value = self.minimax(board, depth - 1, -float('inf'), float('inf'), False, mines)
            board.pop()

            if board_value > best_value:
                best_value = board_value
                best_move = move

        return best_move

class RandomAgent(SearchAgent):
    pass
