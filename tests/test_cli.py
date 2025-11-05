import json, subprocess, sys, os

def test_cli_smoke(tmp_path):
    recipes_path = tmp_path / "recipes.json"
    data = [
        {"id":"x","name":"X","tags":["vege"],"time_min":10,"budget_eur":2.0,
         "ingredients":[{"name":"pâtes","qty":100,"unit":"g"}]}
    ]
    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    out_path = tmp_path / "out.json"
    cmd = [sys.executable, "-m", "mealmaker.cli", "--recipes", str(recipes_path), "--days", "1", "--output", str(out_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert out_path.exists()
    out = json.loads(out_path.read_text(encoding="utf-8"))
    assert out["days"] == 1
    assert len(out["menu"]) == 1