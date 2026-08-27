"""Montagem do HTML final a partir do template + código gerado."""

from __future__ import annotations

from pathlib import Path

from .models import ConceptSpec

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
MARK_OPEN = "/* ===== GAME CODE (gerado) ===== */"
MARK_CLOSE = "/* ===== FIM GAME CODE ===== */"


def build_html(game_js: str, spec: ConceptSpec) -> str:
    html = (TEMPLATES_DIR / "game.html").read_text(encoding="utf-8")
    colors = (spec.palette.colors + ["#111111"] * 5)[:5]
    html = html.replace("__TITLE__", spec.name)
    for i, c in enumerate(colors):
        html = html.replace(f"__COLOR{i}__", c.replace("#", "%23"))
    html = html.replace("/*__GAME__*/", f"{MARK_OPEN}\n{game_js}\n{MARK_CLOSE}")
    return html


def extract_game_js(html: str) -> str:
    start = html.find(MARK_OPEN)
    end = html.find(MARK_CLOSE)
    if start == -1 or end == -1:
        return html
    return html[start + len(MARK_OPEN) : end]
