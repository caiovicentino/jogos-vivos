"""CLI da fábrica: `python -m fabrica.cli run|graph`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from . import graph as graph_mod
from .llm import LLM
from .mock import MockLLM
from .models import GateReport, slugify
from .nodes import seed
from .template import build_html  # noqa: F401 — exposto p/ testes

console = Console()


def load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def cmd_run(args: argparse.Namespace) -> int:
    load_dotenv()
    llm = MockLLM() if args.mock else LLM()
    app = graph_mod.build(llm)

    state_db = seed.load_state()
    s = seed.pick(state_db, args.seed_idx)
    console.print(Panel.fit(f"[bold]seed:[/bold] {s.id} — {s.mechanic} · {s.theme}", border_style="cyan"))

    final = app.invoke(
        {"seed": s.model_dump(), "iteration": 0},
        config={"recursion_limit": 50},
    )
    gate = GateReport(**final["gate"])
    spec = final["spec"]
    slug = slugify(spec["name"] if isinstance(spec, dict) else spec.name)
    out = Path(args.out) / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(final["code_html"], encoding="utf-8")

    report = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mock": args.mock,
        "seed": s.model_dump(),
        "spec": spec,
        "gate": gate.model_dump(),
        "iterations": final["iteration"],
    }
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    seed.record(state_db, s, slug, gate.passed, final["iteration"])

    if gate.passed:
        console.print(f"[bold green]✓ gate passou[/bold green] em {final['iteration']} iteração(ões) → {out / 'index.html'}")
    else:
        console.print(f"[bold red]✗ gate recusou após {final['iteration']} iterações[/bold red]")
        for e in gate.errors:
            console.print(f"  [red]·[/red] [{e.rule}] {e.message}")
    for w in gate.warnings:
        console.print(f"  [yellow]·[/yellow] [{w.rule}] {w.message}")
    return 0 if gate.passed else 1


def cmd_inject(args: argparse.Namespace) -> int:
    """Caminho 'seja você o LLM': concept/design/code prontos, gate decide."""
    import json

    from .models import ConceptSpec, DesignDoc
    from .nodes.gate import gate_node
    from .template import build_html

    load_dotenv()
    spec = ConceptSpec(**json.loads(Path(args.spec).read_text(encoding="utf-8")))
    design = json.loads(Path(args.design).read_text(encoding="utf-8"))
    js = Path(args.code).read_text(encoding="utf-8")
    js = js.strip()
    if js.startswith("```"):
        lines = js.splitlines()
        js = "\n".join(lines[1: len(lines) - 1 if lines[-1].strip().startswith("```") else len(lines)])

    state_db = seed.load_state()
    s = seed.pick(state_db, args.seed_idx)
    final = gate_node(
        {
            "code_html": build_html(js, spec),
            "spec": spec.model_dump(),
            "iteration": 0,
        }
    )
    gate = GateReport(**final["gate"])
    slug = slugify(spec.name)
    out = Path(args.out) / slug

    if not gate.passed:
        console.print(f"[bold red]✗ gate recusou {slug}[/bold red]")
        for e in gate.errors:
            console.print(f"  [red]·[/red] [{e.rule}] {e.message}")
        for w in gate.warnings:
            console.print(f"  [yellow]·[/yellow] [{w.rule}] {w.message}")
        return 1

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(build_html(js, spec), encoding="utf-8")
    report = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "inject",
        "seed": s.model_dump(),
        "spec": spec.model_dump(),
        "design": design,
        "gate": gate.model_dump(),
        "iterations": final["iteration"],
    }
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    seed.record(state_db, s, slug, True, final["iteration"])
    console.print(f"[bold green]✓ gate passou[/bold green] → {out / 'index.html'}")
    for w in gate.warnings:
        console.print(f"  [yellow]·[/yellow] [{w.rule}] {w.message}")
    return 0


def cmd_graph(_args: argparse.Namespace) -> int:
    print(graph_mod.mermaid())
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="jogos-vivos", description="Fábrica de web games vivos")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="fabrica um jogo novo")
    run.add_argument("--mock", action="store_true", help="roda sem LLM, com conteúdo fixo (demo/CI)")
    run.add_argument("--out", default="games", help="diretório de saída")
    run.add_argument("--seed-idx", type=int, default=None, help="força o índice da seed")
    run.set_defaults(func=cmd_run)
    g = sub.add_parser("graph", help="imprime o grafo em mermaid")
    g.set_defaults(func=cmd_graph)
    inj = sub.add_parser("inject", help="injeta concept/design/code prontos no gate (modo 'você é o LLM')")
    inj.add_argument("--spec", required=True, help="JSON do ConceptSpec")
    inj.add_argument("--design", required=True, help="JSON do DesignDoc")
    inj.add_argument("--code", required=True, help="JS do jogo (contrato JV)")
    inj.add_argument("--out", default="games")
    inj.add_argument("--seed-idx", type=int, default=None)
    inj.set_defaults(func=cmd_inject)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
