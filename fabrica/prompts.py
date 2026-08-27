"""Carregador de prompts versionados em prompts/*.md."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from . import anti_slop

# prompts/ fica na raiz do repo (histórico legível no GitHub)
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load(name: str) -> str:
    text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    return text.replace("{ANTI_SLOP}", anti_slop.as_prompt_rules())
