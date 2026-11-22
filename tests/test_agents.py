import unittest

import chess

from chess_minesweeper.agents import RandomAgent, SearchAgent


class AgentTests(unittest.TestCase):
    def test_agents_return_legal_moves_and_leave_the_board_intact(self):
        board = chess.Board()
        board.push_san("e4")
        initial_fen, initial_stack = board.fen(), list(board.move_stack)
        for agent in (RandomAgent(seed=42), SearchAgent(seed=42)):
            with self.subTest(agent=type(agent).__name__):
                self.assertIn(agent.choose_move(board, frozenset(), 3), board.legal_moves)
                self.assertEqual(board.fen(), initial_fen)
                self.assertEqual(board.move_stack, initial_stack)

    def test_search_avoids_a_known_mine_when_material_is_equal(self):
        board = chess.Board("4k2r/8/8/8/8/8/8/R3K3 w Qk - 0 9")
        preferred_move = SearchAgent(seed=2, depth=1).choose_move(board, frozenset(), 1)
        mines = frozenset({preferred_move.to_square})
        move = SearchAgent(seed=2, depth=1).choose_move(board, mines, 1)
        self.assertNotIn(move.to_square, mines)
