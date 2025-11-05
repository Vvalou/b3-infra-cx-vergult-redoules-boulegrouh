import pytest
from mealmaker.core import (
    is_vege,
    is_viande,
    fits_time,
    within_budget_avg,
    select_menu,
    consolidate_shopping_list,
)

# ---- Helpers -------------------------------------------------------------

def R(tags, ings=None, t=20, b=2.0, rid=None, name=None):
    return {
        "id": rid or (name or "X"),
        "name": name or (rid or "X"),
        "tags": tags,
        "time_min": t,
        "budget_eur": b,
        "ingredients": [{"name": i, "qty": 100, "unit": "g"} for i in (ings or [])],
    }

def sample_recipes():
    return [
        R(["vege"], ings=["pâtes"], t=15, b=2.0, rid="r1", name="A"),
        R(["viande"], ings=["riz"], t=30, b=3.0, rid="r2", name="B"),
        R(["vege"], ings=["pâtes"], t=10, b=1.5, rid="r3", name="C"),
    ]

# ---- Tests de base (reprennent vos contrôles) ---------------------------

def test_is_vege():
    assert is_vege({"tags": ["VeGe"]}) is True
    assert is_vege({"tags": ["viande"]}) is False

def test_fits_time():
    assert fits_time({"time_min": 20}, 30) is True
    assert fits_time({"time_min": 40}, 30) is False
    assert fits_time({"time_min": 40}, None) is True

def test_within_budget_avg():
    recs = [{"budget_eur": 2.0}, {"budget_eur": 4.0}]
    assert within_budget_avg(recs, 3.0, 0.2) is True
    assert within_budget_avg(recs, 2.0, 0.1) is False

def test_select_menu_constraints_basic():
    recs = sample_recipes()
    menu = select_menu(recs, days=3, min_vege=2, max_time=30, avg_budget=2.0, tolerance=0.5, seed=1)
    assert len(menu) == 3
    assert sum(1 for r in menu if is_vege(r)) >= 2
    avg = sum(r["budget_eur"] for r in menu) / len(menu)
    assert (2.0 * 0.5) <= avg <= (2.0 * 1.5)

def test_consolidate_shopping_list():
    recs = sample_recipes()
    items = consolidate_shopping_list(recs[:2])  # r1+r2
    lookup = {(i["name"], i["unit"]): i["qty"] for i in items}
    assert lookup.get(("pâtes", "g")) == 100  # de r1
    assert lookup.get(("riz", "g")) == 100    # de r2

# ---- Nouvelles fonctionnalités ------------------------------------------

def _recipes_rich():
    recs = []
    # 6 vege
    for i in range(1, 7):
        recs.append(R(["vege"], ings=["pâtes"], t=12+i, b=2.0, rid=f"vg{i}", name=f"Vege {i}"))
    # 4 viande (dont 2 avec "porc" et 1 avec "lait")
    recs.append(R(["viande"], ings=["boeuf"], t=25, b=3.0, rid="me1", name="Viande 1"))
    recs.append(R(["viande"], ings=["porc"],  t=22, b=3.2, rid="me2", name="Viande 2"))
    recs.append(R(["viande"], ings=["poulet"],t=28, b=3.1, rid="me3", name="Viande 3"))
    recs.append(R(["viande"], ings=["lait"],  t=18, b=2.8, rid="me4", name="Viande 4"))
    return recs

def test_min_viande_enforced():
    recs = _recipes_rich()
    menu = select_menu(recs, days=5, min_vege=2, min_viande=2, seed=0)
    assert len(menu) == 5
    viande = sum(1 for r in menu if is_viande(r))
    vege   = sum(1 for r in menu if is_vege(r))
    assert viande >= 2
    assert vege   >= 2

def test_max_viande_enforced():
    recs = _recipes_rich()
    menu = select_menu(recs, days=5, min_vege=2, max_viande=1, seed=1)
    assert len(menu) == 5
    viande = sum(1 for r in menu if is_viande(r))
    assert viande <= 1

def test_min_ceil_max_floor_effect():
    recs = _recipes_rich()
    # min_viande=1.5 => exige au moins 2 ; max_viande=2.9 => autorise au plus 2
    menu = select_menu(recs, days=5, min_vege=1, min_viande=1.5, max_viande=2.9, seed=2)
    viande = sum(1 for r in menu if is_viande(r))
    assert viande == 2

def test_exclude_ingredients_filters():
    recs = _recipes_rich()
    menu = select_menu(recs, days=5, exclude_ingredients=["lait", "porc"], seed=3)
    assert len(menu) == 5
    flat_ings = [ing["name"].lower() for r in menu for ing in r.get("ingredients", [])]
    assert all("lait" not in x for x in flat_ings)
    assert all("porc" not in x for x in flat_ings)

def test_no_duplicates_true():
    recs = [
        R(["vege"], rid="a", name="A"),
        R(["viande"], rid="b", name="B"),
        R(["vege"], rid="c", name="C"),
    ]
    menu = select_menu(recs, days=3, seed=4, no_duplicates=True)
    ids = [r["id"] for r in menu]
    assert len(ids) == len(set(ids))
