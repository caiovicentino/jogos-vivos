import json

from fabrica import graph as graph_mod
from fabrica.mock import MockLLM
from fabrica.nodes import seed as seed_mod


def test_full_graph_mock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # state.json isolado
    app = graph_mod.build(MockLLM())
    s = seed_mod.pick({"runs": []}, 0)
    final = app.invoke({"seed": s.model_dump(), "iteration": 0}, config={"recursion_limit": 50})
    assert final["gate"]["passed"], final["gate"]["errors"]
    assert final["code_html"].startswith("<!doctype html>")
    assert "JV.config" in final["code_html"]


def test_seed_rotation_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seeds = seed_mod.load_seeds()
    assert len(seeds) >= 30
    a = seed_mod.pick({"runs": []}, None)
    state = {"runs": [{"x": 1} for _ in range(5)]}
    b = seed_mod.pick(state, None)
    assert a.id != b.id or len(seeds) == 1
    # registro em state.json
    seed_mod.record(state, b, "slug-teste", True, 1)
    data = json.loads(seed_mod.STATE_FILE.read_text(encoding="utf-8"))
    assert data["runs"][-1]["slug"] == "slug-teste"
