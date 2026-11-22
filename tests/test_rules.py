import unittest

import chess

from chess_minesweeper.rules import Game, MineMode

OPENING = (
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 d7d6 c2c3 e8g8"
).split()


def mined_game(fen, mines, mode=MineMode.CLASSIC):
    game = Game(mode, seed=42, board=chess.Board(fen))
    game.mines = set(mines)
    return game


class GameTests(unittest.TestCase):
    def test_mines_activate_after_exactly_sixteen_plies(self):
        for mode, expected_count in ((MineMode.CLASSIC, 12), (MineMode.RELOCATING, 4)):
            with self.subTest(mode=mode):
                game = Game(mode, seed=42)
                for uci in OPENING[:-1]:
                    game.play(chess.Move.from_uci(uci))
                    self.assertFalse(game.mines_active)
                    self.assertFalse(game.mines)
                result = game.play(chess.Move.from_uci(OPENING[-1]))
                self.assertEqual(game.ply, 16)
                self.assertTrue(game.mines_active)
                self.assertEqual(len(game.mines), expected_count)
                self.assertTrue(game.mines.isdisjoint(game.board.piece_map()))
                self.assertEqual(result.blasts, ())

    def test_destroyed_double_step_pawn_cannot_be_captured_en_passant(self):
        game = mined_game("r3k3/8/8/8/3p4/8/4P3/R3K3 w Qq - 0 9", [chess.E4])
        self.assertEqual(game.hint(chess.D4), 1)
        result = game.play(chess.Move.from_uci("e2e4"))
        self.assertEqual(result.blasts, (chess.E4,))
        self.assertIsNone(game.board.piece_at(chess.E4))
        self.assertIsNone(game.board.ep_square)
        self.assertEqual(game.hint(chess.D4), 0)
        self.assertEqual(len(game.board.move_stack), 0)
        self.assertTrue(game.board.is_valid())

    def test_classic_king_respawns_and_loses_a_life(self):
        game = mined_game("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 9", [chess.E2])
        game.play(chess.Move.from_uci("e1e2"))
        self.assertEqual(game.board.king(chess.WHITE), chess.E1)
        self.assertEqual(game.king_lives[chess.WHITE], 2)
        self.assertFalse(game.board.has_castling_rights(chess.WHITE))
        self.assertIsNone(game.end_message)

    def test_relocating_king_stays_and_mine_moves_to_a_different_empty_square(self):
        game = mined_game(
            "r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 9",
            [chess.E2, chess.D4, chess.B2, chess.C7],
            MineMode.RELOCATING,
        )
        game.play(chess.Move.from_uci("e1e2"))
        self.assertEqual(game.board.king(chess.WHITE), chess.E2)
        self.assertEqual(game.king_lives[chess.WHITE], 2)
        self.assertEqual(len(game.mines), 4)
        self.assertNotIn(chess.E2, game.mines)
        self.assertTrue(game.mines.isdisjoint(game.board.piece_map()))

    def test_castling_triggers_mines_at_both_destinations(self):
        game = mined_game(
            "r3k3/8/8/8/8/8/8/R3K2R w KQq - 0 9",
            [chess.F1, chess.G1],
        )
        result = game.play(chess.Move.from_uci("e1g1"))
        self.assertEqual(result.blasts, (chess.G1, chess.F1))
        self.assertIsNone(game.board.piece_at(chess.F1))
        self.assertEqual(game.board.king(chess.WHITE), chess.E1)
        self.assertEqual(game.king_lives[chess.WHITE], 2)

    def test_blast_that_exposes_moving_king_ends_the_game(self):
        game = mined_game("4r1k1/8/8/8/8/4R3/8/4K3 w - - 0 9", [chess.E4])
        game.play(chess.Move.from_uci("e3e4"))
        self.assertEqual(game.end_message, "Black wins. A blast exposed White's king.")

    def test_last_king_life_ends_the_game(self):
        game = mined_game("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 9", [chess.E2])
        game.king_lives[chess.WHITE] = 1
        game.play(chess.Move.from_uci("e1e2"))
        self.assertEqual(game.king_lives[chess.WHITE], 0)
        self.assertEqual(game.end_message, "Black wins. White's king ran out of lives.")

    def test_illegal_move_is_rejected_without_advancing_the_game(self):
        game = Game()
        with self.assertRaises(ValueError):
            game.play(chess.Move.from_uci("e2e5"))
        self.assertEqual(game.ply, 0)
        self.assertEqual(game.board.fen(), chess.Board().fen())

    def test_checkmate_and_stalemate_end_the_game(self):
        game = Game()
        for uci in ("f2f3", "e7e5", "g2g4", "d8h4"):
            game.play(chess.Move.from_uci(uci))
        self.assertEqual(game.end_message, "Black wins by checkmate.")
        with self.assertRaises(ValueError):
            game.play(chess.Move.from_uci("e2e4"))

        stalemate = Game(board=chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"))
        self.assertEqual(stalemate.end_message, "Draw by stalemate.")
