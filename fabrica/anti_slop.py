"""Regras anti-slop — fonte única usada tanto pelos prompts quanto pelo gate.

Baseado em: Wikipedia:Signs of AI writing, guidelines de qualidade do
CrazyGames e no consenso de r/gamedev (IA no código sim, no soul não).
"""

from __future__ import annotations

import re
from typing import Any

# (rule_id, regex, nível, mensagem)
BANNED: list[tuple[str, str, str, str]] = [
    ("em_dash", r"—", "error", "em-dash é tell de texto IA; reescreva com vírgula ou ponto."),
    ("not_just_but", r"not just\s+.{0,40}\bbut\b", "error", "construção 'not just X but Y' é tell clássico de IA."),
    ("delve", r"\bdelve\b", "error", "palavra-banida de copy IA."),
    ("testament", r"\btestament\b", "error", "palavra-banida de copy IA."),
    ("pivotal", r"\bpivotal\b", "error", "palavra-banida de copy IA."),
    ("elevate", r"\belevate\b", "error", "puffery vazio, tell de IA."),
    ("unleash", r"\bunleash\b", "error", "puffery vazio, tell de IA."),
    ("in_conclusion", r"\bin conclusion\b", "error", "estrutura de texto gerado."),
    ("gradient", r"linear-gradient|radial-gradient", "error", "gradiente gratuito é tell visual de IA; use a paleta fixa."),
    ("emoji", r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "error", "emoji não é sprite; desenhe ou use a paleta."),
    ("default_purple", r"#(8b5cf6|7c3aed|6d28d9|a78bfa)\b", "warning", "roxo default de IA detectado na paleta."),
    ("console_log", r"console\.log", "warning", " deixe o build limpo: remova console.log."),
]

PROMPT_RULES = """\
## Regras anti-slop (invioláveis)
1. UMA mecânica central. Se ela não cabe em 30 segundos de explicação, está grande demais.
2. Copy do jogo (título, tagline, HUD, game over) em pt-BR, curto, com voz — nunca em inglês genérico.
3. NADA de: em-dash, "not just X but Y", delve, testament, pivotal, elevate, unleash.
4. NADA de gradientes CSS ou emoji como sprite. A paleta fixa define TUDO.
5. Nada de roxo/azul default. A paleta vem do concept e é lei.
6. Consistência: menu, jogo e game over compartilham o mesmo estilo (o shell do template cuida disso).
7. Juice mínimo: ao menos um efeito de feedback por ação importante (som + partícula + shake se couber).
8. Nome minúsculo, esquisito, específico — no estilo de "holedown" ou "downwell". Nunca descritivo-genérico.
"""


def check_text(text: str) -> list[tuple[str, str, str]]:
    """Retorna [(rule, level, message)] para todo o texto dado."""
    found: list[tuple[str, str, str]] = []
    for rule, pattern, level, msg in BANNED:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append((rule, level, msg))
    return found


def as_prompt_rules() -> str:
    return PROMPT_RULES


def check_structure(html: str, game_js: str, spec: Any) -> list[tuple[str, str, str]]:
    """Checagens estruturais do jogo gerado contra o concept.

    `game_js` é só o código gerado: o template injeta a paleta no CSS,
    então a prova de uso real da paleta está no JS do jogo.
    """
    issues: list[tuple[str, str, str]] = []
    low = html.lower()
    jslow = game_js.lower()
    if len(html) > 300_000:
        issues.append(("size", "error", "jogo maior que 300KB; escopo está fora de controle."))
    if "jv.config" not in jslow:
        issues.append(("contract", "error", "JV.config não definido: o jogo não fala a língua do template."))
    if not re.search(r"\bupdate\s*[=:(]", jslow) or not re.search(r"\bdraw\s*[=:(]", jslow):
        issues.append(("contract", "error", "JV.game precisa de update(dt) e draw(ctx)."))
    for color in spec.palette.colors:
        if color not in jslow:
            issues.append(("palette", "error", f"paleta declarada mas cor {color} não usada no jogo."))
            break
    return issues
