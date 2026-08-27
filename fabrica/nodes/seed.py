"""Nó SEED — escolha determinística do tema do dia (rotação sobre state.json)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..models import Seed

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = Path("state/state.json")


def load_seeds() -> list[dict]:
    raw = yaml.safe_load((DATA_DIR / "seeds.yaml").read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else raw.get("seeds", [])


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"runs": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def pick(state: dict, idx: int | None = None) -> Seed:
    seeds = load_seeds()
    if not seeds:
        raise RuntimeError("seeds.yaml vazio")
    i = idx if idx is not None else state.get("runs", []).__len__() % len(seeds)
    return Seed(**seeds[i % len(seeds)])


def record(state: dict, seed: Seed, slug: str, passed: bool, iterations: int) -> None:
    state.setdefault("runs", []).append(
        {
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "seed_id": seed.id,
            "slug": slug,
            "gate_passed": passed,
            "iterations": iterations,
        }
    )
    save_state(state)
