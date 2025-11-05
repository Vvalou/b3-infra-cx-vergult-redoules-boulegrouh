from typing import Any, Dict, List, Tuple
import math
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
    no_duplicates: bool = False,  # <<< première modif : option anti-doublons
) -> List[Dict[str, Any]]:
    """
    Sélection simple et déterministe (via seed) :
    - Filtre par temps.
    - Tire au sort jusqu'à avoir 'days' recettes.
    - Vérifie min_vege et budget moyen (si fourni). Réessaie quelques fois.
    - Peut éviter les doublons si no_duplicates=True.
    """
    pool = [r for r in recipes if fits_time(r, max_time)]
    if seed is not None:
        random.seed(seed)
    attempts = 200
    best: List[Dict[str, Any]] = []
    for _ in range(attempts):
        if len(pool) >= days:
            # Tirage sans remplacement => pas de doublons
            cand = random.sample(pool, k=days)
        else:
            if no_duplicates:
                # Pas assez de recettes uniques : on prend tout le pool
                cand = pool[:]
            else:
                # Ancien comportement : compléter par tirage avec remplacement
                cand = pool[:]
                while len(cand) < days and pool:
                    cand.append(random.choice(pool))

        # Contraintes
        vege_count = sum(1 for r in cand if is_vege(r))
        if vege_count < min_vege:
            continue
        if avg_budget is not None and not within_budget_avg(cand, avg_budget, tolerance):
            continue
        best = cand
        break

    if not best:
        # Dernier recours: prendre les premiers qui passent le temps
        # Fallback (2ᵉ modif) : respecter no_duplicates
        if no_duplicates:
            # On renvoie au mieux des recettes uniques (peut être < days s'il n'y en a pas assez)
            best = pool[:days] if len(pool) >= days else pool[:]
        else:
            # Comportement historique : compléter par duplication si nécessaire
            best = pool[:days] if len(pool) >= days else (pool + pool)[:days]
        best = pool[:days] if len(pool) >= days else (pool + pool)[:days]
    return best

def consolidate_shopping_list(menu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrège par (name, unit). Ne gère pas la conversion d’unités (simple au départ).
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
    no_duplicates: bool = False,  # <<< première modif : passe-plat
) -> Dict[str, Any]:
    menu = select_menu(
        recipes, days=days, min_vege=min_vege, max_time=max_time,
        avg_budget=avg_budget, tolerance=tolerance, seed=seed,
        no_duplicates=no_duplicates
    )
    shopping = consolidate_shopping_list(menu)
    return {"days": days, "menu": menu, "shopping_list": shopping}
