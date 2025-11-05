from typing import Any, Dict, List, Tuple, Optional
import math
import random


def is_vege(recipe: Dict[str, Any]) -> bool:
    return "tags" in recipe and any(t.lower() == "vege" for t in recipe["tags"])


def is_viande(recipe: Dict[str, Any]) -> bool:
    # Ajuste selon tes tags (ex: {"viande","meat","boeuf","poulet"})
    return "tags" in recipe and any(t.lower() in {"viande", "meat"} for t in recipe["tags"])


def fits_time(recipe: Dict[str, Any], max_time: Optional[int]) -> bool:
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
    min_vege: Optional[int] = 2,
    max_time: Optional[int] = None,
    avg_budget: Optional[float] = None,
    tolerance: float = 0.2,
    seed: Optional[int] = 42,
    min_viande: Optional[float] = None,  # float accepté (ceil)
    max_viande: Optional[float] = None,  # float accepté (floor)
) -> List[Dict[str, Any]]:
    """
    Sélection simple et déterministe (via seed) :
    - Filtre par temps.
    - Échantillonne jusqu'à 'days' recettes (complète si dataset petit).
    - Vérifie min_vege, min_viande, max_viande et budget moyen (si fournis).
    """
    # Normalisations & validations
    if isinstance(min_viande, float):
        min_viande = math.ceil(min_viande)
    if isinstance(max_viande, float):
        max_viande = math.floor(max_viande)
    if isinstance(min_vege, float):
        min_vege = math.ceil(min_vege)

    if min_vege is not None and min_vege < 0:
        raise ValueError("min_vege doit être >= 0")
    if min_viande is not None and min_viande < 0:
        raise ValueError("min_viande doit être >= 0")
    if max_viande is not None and max_viande < 0:
        raise ValueError("max_viande doit être >= 0")

    if max_viande is not None and max_viande > days:
        raise ValueError("max_viande ne peut pas dépasser le nombre de jours")

    if min_viande is not None and max_viande is not None and min_viande > max_viande:
        raise ValueError(f"Incohérent: min_viande({min_viande}) > max_viande({max_viande})")

    # NB: on ne peut pas déduire mathématiquement l'infaisabilité vs min_vege ici
    # sans connaître la proportion de recettes disponibles par catégorie.

    pool = [r for r in recipes if fits_time(r, max_time)]
    if seed is not None:
        random.seed(seed)

    attempts = 200
    best: List[Dict[str, Any]] = []

    for _ in range(attempts):
        if not pool:
            break

        # Tirage de base
        cand = random.sample(pool, k=min(days, len(pool))) if len(pool) >= days else pool[:]

        # Complète si nécessaire (petit dataset)
        while len(cand) < days and pool:
            cand.append(random.choice(pool))

        # Contraintes
        if min_vege is not None:
            vege_count = sum(1 for r in cand if is_vege(r))
            if vege_count < min_vege:
                continue

        viande_count = sum(1 for r in cand if is_viande(r))
        if min_viande is not None and viande_count < min_viande:
            continue
        if max_viande is not None and viande_count > max_viande:
            continue

        if avg_budget is not None and not within_budget_avg(cand, avg_budget, tolerance):
            continue

        best = cand
        break

    if not best:
        # Fallback raisonnable
        best = pool[:days] if len(pool) >= days else (pool + pool)[:days]

    return best


def consolidate_shopping_list(menu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrège par (name, unit). Pas de conversion d’unités.
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
    min_vege: Optional[int] = 2,
    max_time: Optional[int] = None,
    avg_budget: Optional[float] = None,
    tolerance: float = 0.2,
    seed: Optional[int] = 42,
    min_viande: Optional[float] = None,
    max_viande: Optional[float] = None,
) -> Dict[str, Any]:
    menu = select_menu(
        recipes=recipes,
        days=days,
        min_vege=min_vege,
        max_time=max_time,
        avg_budget=avg_budget,
        tolerance=tolerance,
        seed=seed,
        min_viande=min_viande,
        max_viande=max_viande,
    )
    shopping = consolidate_shopping_list(menu)
    return {"days": days, "menu": menu, "shopping_list": shopping}
