"""MockLLM: roda o grafo inteiro offline (CI, demo, testes)."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from .models import ConceptSpec, DesignDoc, Palette

T = TypeVar("T", bound=BaseModel)

MOCK_GAME = r"""
JV.config = { name: "sinal-vermelho", tagline: "pise, pare, respire. repita.",
  palette: ["#f4f1de", "#e07a5f", "#3d405b", "#81b29a", "#0b0b0e"], font: "VT323" };
JV.game.slug = "sinal-vermelho";

const keys = {};
let px = 0, dardo = null, blocos = [];
JV.game.init = () => {
  px = JV.W / 2; dardo = null; blocos = [];
  for (let i = 0; i < 4; i++) blocos.push(novoBloco(i));
};
function novoBloco(i) {
  const rng = JV.rng((Date.now() + i * 977) >>> 0);
  return { x: rng() * JV.W, y: -40 - rng() * JV.H * 0.6, v: 60 + rng() * 60, r: 10 + rng() * 14 };
}
JV.game.update = (dt) => {
  if (keys.left) px -= 240 * dt;
  if (keys.right) px += 240 * dt;
  px = Math.max(14, Math.min(JV.W - 14, px));
  for (const b of blocos) {
    b.y += b.v * dt;
    if (b.y > JV.H + 40) Object.assign(b, novoBloco(0));
    if (Math.hypot(b.x - px, b.y - (JV.H - 60)) < b.r + 14) {
      JV.sfx("explode"); JV.shake(10); JV.burst(px, JV.H - 60, JV.config.palette[1], 26); JV.gameover();
    }
  }
  if (dardo) {
    dardo.y -= 420 * dt;
    for (const b of blocos) {
      if (Math.hypot(b.x - dardo.x, b.y - dardo.y) < b.r + 6) {
        JV.sfx("hit"); JV.burst(b.x, b.y, JV.config.palette[3], 14);
        JV.score += 10; dardo = null; Object.assign(b, novoBloco(0));
        break;
      }
    }
  }
};
JV.game.draw = (ctx) => {
  ctx.fillStyle = JV.config.palette[4]; ctx.fillRect(0, 0, JV.W, JV.H);
  ctx.fillStyle = JV.config.palette[3];
  ctx.fillRect(px - 14, JV.H - 54, 28, 28);
  ctx.fillStyle = JV.config.palette[1];
  for (const b of blocos) { ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, 7); ctx.fill(); }
  if (dardo) { ctx.fillStyle = JV.config.palette[0]; ctx.fillRect(dardo.x - 3, dardo.y - 16, 6, 20); }
  JV.text("pontos " + JV.score, 12, 24, 18, JV.config.palette[0], "left");
};
JV.game.onKey = (k, down) => { keys[k] = down; };
JV.game.onPointer = (x, y, phase) => {
  px = x;
  if (phase === "down" && !dardo) { dardo = { x: px, y: JV.H - 70 }; JV.sfx("shoot"); }
};
"""


class MockLLM:
    """Mesma interface de LLM, respostas determinísticas. Para testes e demo."""

    def __init__(self, *args, **kwargs):  # noqa: ARG002 — assinatura compatível
        pass

    def json(self, system: str, user: str, schema: type[T], **kw):  # noqa: ANN001, ARG002
        if schema is ConceptSpec:
            return ConceptSpec(
                name="sinal-vermelho",
                tagline="pise, pare, respire. repita.",
                genre="arcade",
                mechanic="desviar de blocos que caem e rebater dardos",
                controls="setas/WASD + espaço",
                palette=Palette(name="noturno-4", colors=["#f4f1de", "#e07a5f", "#3d405b", "#81b29a", "#0b0b0e"]),
                juice=["screenshake ao morrer", "partículas ao estourar bloco", "som em cada dardo"],
                first_minute="blocos caem lento, ritmo dobra aos 30s",
                anti_slop=["nome minúsculo e específico", "paleta nomeada de 5 cores"],
            )
        if schema is DesignDoc:
            return DesignDoc(
                core_loop="desviar de blocos; atirar dardo; somar pontos por bloco estourado",
                entities=["jogador (retângulo 28px)", "blocos que caem", "dardo"],
                scoring="+10 por bloco; nada de combo",
                difficulty="velocidade dos blocos sobe 10% a cada 15s",
                states=["menu", "jogando", "game over"],
                juice_checklist=["JV.shake na morte", "JV.burst no hit", "JV.sfx no tiro"],
                failure="toque em bloco encerra com shake e explosão de partículas",
            )
        raise RuntimeError(f"Mock não sabe responder {schema.__name__}")

    def text(self, system: str, user: str) -> str:  # noqa: ARG002
        return MOCK_GAME
