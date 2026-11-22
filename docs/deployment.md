# Deployment

Chess Minesweeper ships as a Python desktop application. The release artifacts are a wheel and a source distribution. A graphical desktop is required for interactive play.

## Build and verify locally

Activate a virtual environment and run these commands from the project root.

```sh
python -m pip install ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
python -m build
```

`dist/` contains a `chess_minesweeper-0.1.0-py3-none-any.whl` and a `chess_minesweeper-0.1.0.tar.gz`. For a release check, activate a fresh virtual environment and install the wheel there.

```sh
python -m pip install dist/chess_minesweeper-0.1.0-py3-none-any.whl
python -m pip check
chess-minesweeper --smoke-test
chess-minesweeper --mode relocating --opponent local
```

For a machine with no graphical session, set `SDL_VIDEODRIVER=dummy` before the smoke test. In PowerShell, use `$env:SDL_VIDEODRIVER = 'dummy'`. Unset it before playing interactively.

If Pygame reports that no video device is available during normal play, launch from a graphical session and check that `SDL_VIDEODRIVER` is unset. Sound is optional. The app uses labeled, color-coded pieces when a chess-symbol font is unavailable.

## GitHub review and release

Before publishing, confirm repository visibility and the license for the project source. The upstream dependencies retain their own licenses. [python-chess license](https://github.com/niklasf/python-chess/blob/master/LICENSE.txt), [Pygame license information](https://pypi.org/project/pygame/2.6.1/).

Once the files have been reviewed, create an empty GitHub repository. In a checkout without Git metadata, initialize `main`, check the exact staged files, and make the first commit. Use the HTTPS or SSH URL of the repository you created in place of `YOUR_REPOSITORY_URL`.

```sh
git init -b main
git add .
git diff --cached --stat
git diff --cached --check
git commit -m "Prepare Chess Minesweeper desktop package"
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

The staged list should include the package, tests, docs, experiments, and CI workflow. `.gitignore` filters virtual environments, generated notebook output, model weights, compiled binaries, and build artifacts.

[GitHub Actions](../.github/workflows/ci.yml) builds the distributions, tests the installed wheel, and runs a headless launch on Linux, Windows, and macOS. Download `chess-minesweeper-distribution` from a successful run. When preparing a release, bump the version in `pyproject.toml`, use the corresponding wheel filename, and attach the wheel and source archive to the GitHub release. A user installs the downloaded wheel with `python -m pip install <wheel-file>` and launches `chess-minesweeper`.
