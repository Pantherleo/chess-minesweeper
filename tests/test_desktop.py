import os
import unittest
from concurrent.futures import Future
from unittest.mock import patch

import chess
import pygame

from chess_minesweeper.desktop import DesktopGame, square_at, square_rect
from chess_minesweeper.rules import Game, MineMode


class DesktopTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(pygame.quit)

    def make_app(self, opponent="local"):
        app = DesktopGame(MineMode.CLASSIC, opponent, seed=3, sound_path=None)
        self.addCleanup(app.worker.shutdown, cancel_futures=True)
        return app

    def test_board_coordinates_and_mouse_move(self):
        app = self.make_app()
        self.assertEqual(square_at((0, 0)), chess.A8)
        self.assertIsNone(square_at((-1, 0)))
        self.assertIsNone(square_at((0, 600)))
        for square in (chess.E2, chess.E4):
            app._handle_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    button=1,
                    pos=square_rect(square).center,
                )
            )
        self.assertEqual(app.game.board.peek().uci(), "e2e4")

    def test_promotion_waits_for_piece_choice(self):
        app = self.make_app()
        app.game = Game(board=chess.Board("6k1/P7/8/8/8/7p/8/6K1 w - - 0 1"))
        app._click(square_rect(chess.A7).center)
        app._click(square_rect(chess.A8).center)
        self.assertEqual(app.game.ply, 0)
        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
        self.assertEqual(app.game.board.piece_at(chess.A8), chess.Piece(chess.KNIGHT, chess.WHITE))

    def test_restart_discards_a_computer_move_already_in_progress(self):
        app = self.make_app("search")
        app._play(chess.Move.from_uci("e2e4"))
        previous_move = Future()
        previous_move.set_running_or_notify_cancel()
        app.ai_move = previous_move
        app.reset()
        previous_move.set_result(chess.Move.from_uci("e7e5"))
        app._update()
        self.assertEqual(app.game.board.fen(), chess.Board().fen())
        self.assertIsNone(app.ai_move)
