from fabrica.anti_slop import check_text
from fabrica.template import build_html, extract_game_js
from fabrica.mock import MOCK_GAME
from fabrica.models import ConceptSpec, Palette

SPEC = ConceptSpec(
    name="sinal-vermelho",
    tagline="pise, pare, respire.",
    genre="arcade",
    mechanic="desviar",
    controls="setas",
    palette=Palette(name="teste", colors=["#f4f1de", "#e07a5f", "#3d405b", "#81b29a", "#0b0b0e"]),
    juice=["shake", "burst"],
    first_minute="lento no começo",
)


def test_banned_words():
    assert any(r == "delve" for r, _, _ in check_text("you delve into"))
    assert any(r == "em_dash" for r, _, _ in check_text("algo — outro algo"))
    assert any(r == "not_just_but" for r, _, _ in check_text("not just a game, but a journey"))
    assert check_text("jogo simples e honesto") == []


def test_gradient_and_emoji_banned():
    assert any(r == "gradient" for r, _, _ in check_text("background: linear-gradient(red, blue)"))
    assert any(r == "emoji" for r, _, _ in check_text("🎉 bingo"))


def test_build_and_extract_roundtrip():
    html = build_html(MOCK_GAME, SPEC)
    assert extract_game_js(html).strip() in MOCK_GAME
    assert "__TITLE__" not in html
    assert "__COLOR0__" not in html
    assert SPEC.palette.colors[0] in html
    assert SPEC.name in html
