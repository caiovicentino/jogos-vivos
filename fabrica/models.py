"""Modelos Pydantic que tipam a passagem de bastão entre os nós do grafo."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, field_validator

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "jogo"


class Palette(BaseModel):
    name: str = Field(description="Nome da paleta no estilo Lospec, ex: 'noturno-4'")
    colors: list[str] = Field(min_length=3, max_length=6)

    @field_validator("colors")
    @classmethod
    def valid_hex(cls, v: list[str]) -> list[str]:
        bad = [c for c in v if not HEX.match(c)]
        if bad:
            raise ValueError(f"cores inválidas (use #RRGGBB): {bad}")
        return [c.lower() for c in v]


class ConceptSpec(BaseModel):
    """Saída do nó CONCEPT — o 'contrato' do jogo."""

    name: str = Field(max_length=18, description="Nome autoral, minúsculo, esquisito: 'holedown', não 'Super Puzzle Deluxe'")
    tagline: str = Field(max_length=90, description="Uma frase curta com voz, pt-BR")
    genre: str
    mechanic: str = Field(description="A ÚNICA mecânica central")
    controls: str = Field(description="Ex: 'setas/WASD + espaço' ou 'toque arrasta'")
    palette: Palette
    juice: list[str] = Field(min_length=2, description="Plano de game-feel: screenshake, hit-stop, partículas...")
    first_minute: str = Field(description="O que acontece nos primeiros 30s de jogo")
    anti_slop: list[str] = Field(default_factory=list, description="Escolhas conscientes para não parecer IA")

    @field_validator("name")
    @classmethod
    def not_generic(cls, v: str) -> str:
        generic = ["super", "deluxe", "mega", "ultimate", "clicker pro", "3d", "simulator"]
        low = v.lower()
        if any(g in low for g in generic):
            raise ValueError(f"nome genérico demais (tell de IA): {v!r}")
        return v.strip()


class DesignDoc(BaseModel):
    """Saída do nó DESIGN — GDD comprimido."""

    core_loop: str
    entities: list[str] = Field(min_length=1, max_length=12)
    scoring: str
    difficulty: str = Field(description="Como a dificuldade sobe nos primeiros 2 minutos")
    states: list[str] = Field(min_length=2, description="ex: menu, jogando, game over")
    juice_checklist: list[str] = Field(min_length=2)
    failure: str = Field(description="Condição de derrota e como ela é comunicada")


class GateIssue(BaseModel):
    level: Literal["error", "warning"]
    rule: str
    message: str


class GateReport(BaseModel):
    passed: bool
    errors: list[GateIssue] = []
    warnings: list[GateIssue] = []

    @property
    def error_text(self) -> str:
        return "\n".join(f"[{e.rule}] {e.message}" for e in self.errors) or "nenhum erro"


class Seed(BaseModel):
    id: str
    genre: str
    mechanic: str
    theme: str
    twist: str
