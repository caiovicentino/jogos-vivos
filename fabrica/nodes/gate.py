"""STATIC GATE — checagem determinística, zero tokens. Porta de entrada da publicação."""

from __future__ import annotations

import shutil
import subprocess
import tempfile

from .. import anti_slop
from ..models import ConceptSpec, GateIssue, GateReport
from ..template import extract_game_js

MAX_ITERATIONS = 3


def _node_check(html: str) -> GateReport:
    """Sintaxe do JS extraído via `node --check` (parse, sem executar)."""
    node = shutil.which("node")
    if not node:
        return GateReport(
            passed=True,
            warnings=[GateIssue(level="warning", rule="node", message="node ausente; checagem de sintaxe pulada.")],
        )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(extract_game_js(html))
        path = f.name
    proc = subprocess.run([node, "--check", path], capture_output=True, text=True)
    if proc.returncode != 0:
        msg = (proc.stderr or "erro de sintaxe").strip().splitlines()[-1]
        return GateReport(passed=False, errors=[GateIssue(level="error", rule="syntax", message=msg)])
    return GateReport(passed=True)


def gate_node(state: dict) -> dict:
    html = state["code_html"]
    spec = ConceptSpec(**state["spec"])
    issues: list[GateIssue] = []

    report = _node_check(html)
    issues.extend(report.errors + report.warnings)

    for rule, level, msg in anti_slop.check_text(html):
        issues.append(GateIssue(level=level, rule=rule, message=msg))
    for rule, level, msg in anti_slop.check_structure(html, extract_game_js(html), spec):
        issues.append(GateIssue(level=level, rule=rule, message=msg))

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    gate = GateReport(passed=not errors, errors=errors, warnings=warnings)
    iteration = state.get("iteration", 0) + 1
    retry = not gate.passed and iteration < MAX_ITERATIONS
    return {"gate": gate.model_dump(), "iteration": iteration, "retry": retry}
