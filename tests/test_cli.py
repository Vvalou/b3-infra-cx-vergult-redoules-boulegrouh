import json, subprocess, sys

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

def _recipes_for_cli():
    recs = []
    # 6 vege
    for i in range(1, 7):
        recs.append({
            "id": f"vg{i}",
            "name": f"Vege {i}",
            "tags": ["vege"],
            "time_min": 10 + i,
            "budget_eur": 2.0,
            "ingredients": [{"name": "pâtes", "qty": 100+i, "unit": "g"}],
        })
    # 4 viande (dont porc & lait pour exclusion)
    recs += [
        {"id":"me1","name":"Viande 1","tags":["viande"],"time_min":20,"budget_eur":3.0,
         "ingredients":[{"name":"boeuf","qty":150,"unit":"g"}]},
        {"id":"me2","name":"Viande 2","tags":["viande"],"time_min":22,"budget_eur":3.2,
         "ingredients":[{"name":"porc","qty":150,"unit":"g"}]},
        {"id":"me3","name":"Viande 3","tags":["viande"],"time_min":25,"budget_eur":3.1,
         "ingredients":[{"name":"poulet","qty":150,"unit":"g"}]},
        {"id":"me4","name":"Viande 4","tags":["viande"],"time_min":18,"budget_eur":2.8,
         "ingredients":[{"name":"lait","qty":200,"unit":"ml"}]},
    ]
    return recs

def _count_viande(menu):
    def is_meat(tags):
        return any(t.lower() == "viande" for t in tags)
    return sum(1 for r in menu if is_meat(r.get("tags", [])))

def _flat_ingredients(menu):
    return [ing["name"].lower() for r in menu for ing in r.get("ingredients", [])]

def test_cli_min_max_viande_range(tmp_path):
    recipes_path = tmp_path / "recipes.json"
    out_path = tmp_path / "out.json"
    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(_recipes_for_cli(), f, ensure_ascii=False)

    cmd = [
        sys.executable, "-m", "mealmaker.cli",
        "--recipes", str(recipes_path),
        "--days", "5",
        "--min-vege", "2",
        "--min-viande", "2",
        "--max-viande", "3",
        "--seed", "42",
        "--output", str(out_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    out = json.loads(out_path.read_text(encoding="utf-8"))
    v = _count_viande(out["menu"])
    assert 2 <= v <= 3

def test_cli_exclude_ingredients(tmp_path):
    recipes_path = tmp_path / "recipes.json"
    out_path = tmp_path / "out.json"
    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(_recipes_for_cli(), f, ensure_ascii=False)

    cmd = [
        sys.executable, "-m", "mealmaker.cli",
        "--recipes", str(recipes_path),
        "--days", "5",
        "--exclude-ingredients", "lait", "porc",
        "--seed", "7",
        "--output", str(out_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    out = json.loads(out_path.read_text(encoding="utf-8"))
    flat = _flat_ingredients(out["menu"])
    assert all("lait" not in x for x in flat)
    assert all("porc" not in x for x in flat)

def test_cli_no_duplicates(tmp_path):
    # 5 recettes uniques, on s'assure que --no-duplicates conserve l'unicité
    recs = [
        {"id":"a","name":"A","tags":["vege"],"time_min":10,"budget_eur":2.0,"ingredients":[]},
        {"id":"b","name":"B","tags":["viande"],"time_min":12,"budget_eur":3.0,"ingredients":[]},
        {"id":"c","name":"C","tags":["vege"],"time_min":14,"budget_eur":2.2,"ingredients":[]},
        {"id":"d","name":"D","tags":["vege"],"time_min":16,"budget_eur":2.4,"ingredients":[]},
        {"id":"e","name":"E","tags":["viande"],"time_min":18,"budget_eur":3.1,"ingredients":[]},
    ]
    recipes_path = tmp_path / "recipes.json"
    out_path = tmp_path / "out.json"
    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False)

    cmd = [
        sys.executable, "-m", "mealmaker.cli",
        "--recipes", str(recipes_path),
        "--days", "5",
        "--no-duplicates",
        "--seed", "1",
        "--output", str(out_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    out = json.loads(out_path.read_text(encoding="utf-8"))
    ids = [r["id"] for r in out["menu"]]
    assert len(ids) == len(set(ids))
