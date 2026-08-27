import json
from pathlib import Path

import pytest

from fabrica.models import ConceptSpec, Palette
from fabrica.nodes.gate import gate_node
from fabrica.template import build_html
from fabrica.mock import MOCK_GAME


def make_spec():
    return ConceptSpec(
        name="sinal-vermelho",
        tagline="pise, pare, respire.",
        genre="arcade",
        mechanic="desviar",
        controls="setas",
        palette=Palette(name="teste", colors=["#f4f1de", "#e07a5f", "#3d405b", "#81b29a", "#0b0b0e"]),
        juice=["shake", "burst"],
        first_minute="lento",
    )


def state_with(html: str, spec=None):
    spec = (spec or make_spec()).model_dump()
    return {"code_html": html, "spec": spec, "iteration": 0}


def test_mock_game_passes_gate():
    from fabrica.template import build_html

    html = build_html(MOCK_GAME, make_spec())
    result = gate_node(state_with(html))
    assert result["gate"]["passed"], json.dumps(result["gate"]["errors"], ensure_ascii=False)


def test_banned_copy_fails_gate(tmp_path: Path):
    html = build_html(MOCK_GAME + '\nconst COPY = "not just a game, but a journey — delve deeper";', make_spec())
    result = gate_node(state_with(html))
    rules = {e["rule"] for e in result["gate"]["errors"]}
    assert "not_just_but" in rules
    assert "em_dash" in rules
    assert not result["gate"]["passed"]


def test_broken_syntax_fails_gate():
    result = gate_node(state_with(build_html("function { quebrado !!!", make_spec())))
    rules = {e["rule"] for e in result["gate"]["errors"]}
    assert "syntax" in rules


def test_palette_unused_fails_gate():
    spec = make_spec()
    spec.palette.colors[2] = "#123456"  # cor declarada que não existe no código
    result = gate_node(state_with(build_html(MOCK_GAME, spec), spec))
    rules = {e["rule"] for e in result["gate"]["errors"]}
    assert "palette" in rules


def test_max_iterations_stops_retry():
    st = state_with("lixo {{{")
    st["iteration"] = 2
    st["code_html"] = build_html("function { quebrado !!!", make_spec())
    result = gate_node(st)
    assert result["retry"] is False
    assert result["iteration"] == 3


@pytest.mark.parametrize("attr", ["update", "draw"])
def test_contract_missing(attr):
    missing = MOCK_GAME.replace(f"JV.game.{attr}", f"JV.game.{attr}_x")
    result = gate_node(state_with(build_html(missing, make_spec())))
    assert not result["gate"]["passed"] or result["gate"]["warnings"]
