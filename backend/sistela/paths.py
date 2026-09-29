"""Immutable bundled resources and mutable per-user data are separate roots."""
import os
import sys
from pathlib import Path

APP_NAME = "SISTELA Assistant"
ROOT = Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    return Path(sys._MEIPASS) if getattr(sys, "frozen", False) else ROOT


def data_dir() -> Path:
    if override := os.environ.get("SISTELA_DATA_DIR"):
        return Path(override).resolve()
    if getattr(sys, "frozen", False):
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise RuntimeError("Windows LOCALAPPDATA is unavailable")
        return (Path(local) / APP_NAME).resolve()
    return ROOT / "data"


def ensure_data_directories(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("documents", "logs", "exports", "backups", "state"):
        (directory / name).mkdir(exist_ok=True)
