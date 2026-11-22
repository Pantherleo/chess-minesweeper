# Experiments

This directory preserves the desktop prototypes, chess-model experiments, and an independent C++ exercise from the original workspace. Use the [desktop package](../README.md) for the maintained game.

| Path | Description |
| --- | --- |
| `legacy/chess1.py` through `legacy/chess4.py` | Early local-play desktop prototypes with different mine rules. `chess3.py` expects its original piece images under `assets/pieces/`. |
| `legacy/game.py`, `legacy/game2.py`, `legacy/agent.py`, `legacy/agent1.py` | Original computer-opponent editions and agent prototypes. The game scripts use Pygame, python-chess, and an audio device. |
| `notebooks/chess.ipynb` | Earlier Pygame implementations. |
| `notebooks/rl.ipynb` and `notebooks/chessnet.ipynb` | Standard-chess experiments with training and self-play. |
| `notebooks/dl2.ipynb` | Standard-chess reinforcement-learning and terminal play experiments. |
| `notebooks/try1.ipynb` | Inference sketch that requires its original `model` module and `chess_engine.pt`. |
| `algorithms/flow.cpp` | Standalone Edmonds–Karp max-flow exercise. |

Notebook copies in this directory have cleared execution outputs. For the training experiments, use a separate Jupyter environment with Python, NumPy, python-chess, and PyTorch. Select the experiment cell you want to run. Several notebooks contain alternative versions of a training loop in different cells.

Local checkpoint files `latest.pth` and `chess_rl_model.pt` are kept in the ignored `models/` directory when available. Some cells look for checkpoints by filename in the kernel's working directory. Point those cells to the appropriate file in `models/` before running them. Use checkpoints from a trusted source. The packaged game uses its own search and random opponents.
