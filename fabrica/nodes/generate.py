"""Nós que chamam LLM: CONCEPT, DESIGN e CODE."""

from __future__ import annotations

from .. import prompts
from ..llm import LLM, strip_fences
from ..models import ConceptSpec, DesignDoc
from ..template import build_html


def concept_node(llm: LLM):
    def run(state: dict) -> dict:
        seed = state["seed"]
        system = prompts.load("concept.system.md")
        user = (
            "Seed do dia (ponto de partida, não prisão):\n"
            f"gênero: {seed['genre']}\nmecânica-base: {seed['mechanic']}\n"
            f"tema: {seed['theme']}\ntwist: {seed['twist']}\n\n"
            "Devolva JSON com: name, tagline, genre, mechanic, controls, "
            "palette {name, colors[3-5]}, juice[], first_minute, anti_slop[]."
        )
        spec = llm.json(system, user, ConceptSpec)
        return {"spec": spec.model_dump()}

    return run


def design_node(llm: LLM):
    def run(state: dict) -> dict:
        spec = ConceptSpec(**state["spec"])
        system = prompts.load("design.system.md")
        user = f"Concept:\n{spec.model_dump_json(indent=2)}"
        doc = llm.json(system, user, DesignDoc)
        return {"design": doc.model_dump()}

    return run


def code_node(llm: LLM):
    def run(state: dict) -> dict:
        spec = ConceptSpec(**state["spec"])
        design = state["design"]
        iteration = state.get("iteration", 0)
        errors = (
            state.get("gate", {}).get("error_text", "")
            if iteration > 0
            else "primeira tentativa, sem erros ainda."
        )
        system = prompts.load("code.system.md")
        user = (
            f"JV.config a preencher (da spec):\n{spec.model_dump_json(indent=2)}\n\n"
            f"Design a implementar:\n{design}\n\n"
            f"Erros do gate para corrigir:\n{errors}"
        )
        js = strip_fences(llm.text(system, user))
        return {"code_html": build_html(js, spec)}

    return run
