# asteroidsgame

A Pygame implementation of the classic arcade game Asteroids (with a couple
creative liberties).

## Requirements

- Python 3.11 (Python 3.11.9 is the tested version)
- The Python packages pinned in `requirements.txt` and `pyproject.toml`

The reproducible environment is currently pinned to Python 3.11 because this
legacy dependency set has been validated with that interpreter version.

## Setup with pip

Python 3.11 is required. On Windows, create and activate a virtual environment
with:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux, use:

```shell
python3.11 -m venv .venv
source .venv/bin/activate
```

Confirm that the active interpreter is Python 3.11, then install the
dependencies and run the game:

```shell
python --version
python -m pip install -r requirements.txt
python asteroidsgame.py
```

## Setup with uv

The `.python-version` and `pyproject.toml` files allow uv to select Python
3.11.9 and install the dependencies automatically:

```shell
uv sync
uv run asteroidsgame.py
```

## Setup with Conda

```shell
conda create --name asteroids python=3.11
conda activate asteroids
python -m pip install -r requirements.txt
python asteroidsgame.py
```
