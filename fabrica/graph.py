"""Definição do grafo LangGraph: concept → design → code → gate (+repair loop)."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .llm import LLM
from .nodes import code_node, concept_node, design_node, gate_node
MAX_ITERATIONS = 3


class GameState(TypedDict, total=False):
    seed: dict
    spec: dict
    design: dict
    code_html: str
    gate: dict
    iteration: int
    retry: bool


def build(llm: LLM):
    g = StateGraph(GameState)
    g.add_node("concept", concept_node(llm))
    g.add_node("design", design_node(llm))
    g.add_node("code", code_node(llm))
    g.add_node("gate", gate_node)
    g.add_edge(START, "concept")
    g.add_edge("concept", "design")
    g.add_edge("design", "code")
    g.add_edge("code", "gate")
    g.add_conditional_edges(
        "gate",
        lambda s: "code" if s.get("retry") else END,
        {"code": "code", END: END},
    )
    return g.compile()


def mermaid() -> str:
    llm = LLM.__new__(LLM)  # grafo é estático; nenhuma chamada é feita
    return build(llm).get_graph().draw_mermaid()
