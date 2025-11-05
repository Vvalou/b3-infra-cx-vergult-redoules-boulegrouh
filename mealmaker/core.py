from typing import Any, Dict, List, Tuple
import random

def is_vege(recipe: Dict[str, Any]) -> bool:
    return "tags" in recipe and any(t.lower() == "vege" for t in recipe["tags"])

def fits_time(recipe: Dict[str, Any], max_time: int | None) -> bool:
    if max_time is None:
        return True
    return int(recipe.get("time_min", 9999)) <= max_time

def within_budget_avg(selected: List[Dict[str, Any]], avg_target: float, tolerance: float = 0.2) -> bool:
    if not selected:
        return True
    cur_avg = sum(float(r.get("budget_eur", 0.0)) for r in selected) / len(selected)
    return (avg_target * (1 - tolerance)) <= cur_avg <= (avg_target * (1 + tolerance))

def select_menu(
    recipes: List[Dict[str, Any]],
    days: int = 7,
    min_vege: int = 2,
    max_time: int | None = None,
    avg_budget: float | None = None,
    tolerance: float = 0.2,
    seed: int | None = 42,
    no_duplicates: bool = False,  # option anti-doublons
) -> List[Dict[str, Any]]:
    """
    - Filtre par temps
    - Tire 'days' recettes (sans remplacement si possible)
    - Vérifie min_vege et budget moyen (si fourni)
    - Respecte no_duplicates dans le tirage et le fallback
    """
    pool = [r for r in recipes if fits_time(r, max_time)]
    if no_duplicates:
      seen = set()
    unique = []
    for r in pool:
        key = r.get("id") or str(r.get("name", "")).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    pool = unique

    if seed is not None:
        random.seed(seed)

    attempts = 200
    best: List[Dict[str, Any]] = []

    for _ in range(attempts):
        if len(pool) >= days:
            # sans remplacement => pas de doublons
            cand = random.sample(pool, k=days)
        else:
            if no_duplicates:
                # pas assez d'uniques : on prend tout le pool (peut être < days)
                cand = pool[:]
            else:
                # compléter en autorisant les doublons
                cand = pool[:]
                while len(cand) < days and pool:
                    cand.append(random.choice(pool))

        # contraintes
        vege_count = sum(1 for r in cand if is_vege(r))
        if vege_count < min_vege:
            continue
        if avg_budget is not None and not within_budget_avg(cand, avg_budget, tolerance):
            continue

        best = cand
        break

    if not best:
        # Fallback qui respecte no_duplicates
        if no_duplicates:
            best = pool[:days] if len(pool) >= days else pool[:]
        else:
            best = pool[:days] if len(pool) >= days else (pool + pool)[:days]

    return best   # ← IMPORTANT : on retourne toujours une liste

def consolidate_shopping_list(menu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrège par (name, unit). Ne gère pas la conversion d’unités.
    """
    agg: Dict[Tuple[str, str], float] = {}
    for r in menu:
        for ing in r.get("ingredients", []):
            key = (ing["name"].strip().lower(), ing.get("unit", "").strip().lower())
            agg[key] = agg.get(key, 0.0) + float(ing.get("qty", 0.0))
    items = [
        {"name": name, "qty": round(qty, 2), "unit": unit}
        for (name, unit), qty in sorted(agg.items())
    ]
    return items

def plan_menu(
    recipes: List[Dict[str, Any]],
    days: int = 7,
    min_vege: int = 2,
    max_time: int | None = None,
    avg_budget: float | None = None,
    tolerance: float = 0.2,
    seed: int | None = 42,
    no_duplicates: bool = False,  # passe-plat
) -> Dict[str, Any]:
    menu = select_menu(
        recipes, days=days, min_vege=min_vege, max_time=max_time,
        avg_budget=avg_budget, tolerance=tolerance, seed=seed,
        no_duplicates=no_duplicates
    )
    shopping = consolidate_shopping_list(menu)
    return {"days": days, "menu": menu, "shopping_list": shopping}
