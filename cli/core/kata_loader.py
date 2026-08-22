"""Load and locate katas."""
import os
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_katas_library() -> Path:
    """Resolve the katas-library folder."""
    if os.getenv("KATAS_LIBRARY"):
        return Path(os.getenv("KATAS_LIBRARY"))
    return PROJECT_ROOT / "katas-library"


def list_katas() -> list[str]:
    lib = get_katas_library()
    if not lib.exists():
        return []
    return sorted([p.name for p in lib.iterdir() if p.is_dir() and (p / "kata.yaml").exists()])


def load_kata(kata_id: str) -> dict:
    path = get_katas_library() / kata_id / "kata.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Kata '{kata_id}' not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_initial_dir(kata_id: str) -> Path:
    return get_katas_library() / kata_id / "initial"
