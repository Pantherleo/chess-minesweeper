# agent.py
import random
import chess

class BaseAgent:
    """
    Base interface for all agents (Random / DRL / Stockfish)
    """
    def __init__(self, color):
        self.color = color

    def get_move(self, board, mines, adjacent_cache):
        raise NotImplementedError


class RandomAgent(BaseAgent):
    """
    Temporary baseline agent.
    Replace this with your DRL agent later.
    """
    def get_move(self, board, mines, adjacent_cache):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        return random.choice(legal_moves)
