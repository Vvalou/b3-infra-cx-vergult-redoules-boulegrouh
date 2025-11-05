from typing import Any, Dict, List, Tuple, Optional
import random

# --- Helpers ---
def normalize(name: str) -> str:
    """Met en minuscules et supprime un 's' final simple pour gérer pluriels."""
    return name.lower().strip().rstrip("s")

def is_vege(recipe: Dict[str, Any]) -> bool:
    return "tags" in recipe and any(t.lower() == "vege" for t in recipe["tags"])

def is_viande(recipe: Dict[str, Any]) -> bool:
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

def fits_exclusions(recipe: Dict[str, Any], exclude_ingredients: Optional[List[str]]) -> bool:
    """Vérifie qu'une recette ne contient pas d'ingrédient à exclure."""
    if not exclude_ingredients:
        return True
    ingredients = [normalize(ing["name"]) for ing in recipe.get("ingredients", [])]
    for excl in exclude_ingredients:
        excl_norm = normalize(excl)
        if any(excl_norm in ing or ing in excl_norm for ing in ingredients):
            return False
    return True

# --- Core functions ---
def select_menu(
    recipes: List[Dict[str, Any]],
    days: int = 7,
    min_vege: Optional[int] = 2,
    max_time: Optional[int] = None,
    avg_budget: Optional[float] = None,
    tolerance: float = 0.2,
    seed: Optional[int] = 42,
    exclude_ingredients: Optional[List[str]] = None,
    min_viande: Optional[int] = None,
    max_viande: Optional[int] = None,
    no_duplicates: bool = False,
) -> List[Dict[str, Any]]:
    """Sélectionne un menu en respectant toutes les contraintes."""
    if seed is not None:
        random.seed(seed)

    # Filtre initial
    pool = [r for r in recipes if fits_time(r, max_time) and fits_exclusions(r, exclude_ingredients)]

    if no_duplicates:
        seen = set()
        unique = []
        for r in pool:
            key = r.get("id") or str(r.get("name", "")).strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(r)
        pool = unique

    if not pool:
        return []

    attempts = 200
    for _ in range(attempts):
        cand = random.sample(pool, k=min(days, len(pool)))
        while len(cand) < days:
            cand.append(random.choice(pool))

        vege_count = sum(1 for r in cand if is_vege(r))
        viande_count = sum(1 for r in cand if is_viande(r))

        if min_vege is not None and vege_count < min_vege:
            continue
        if min_viande is not None and viande_count < min_viande:
            continue
        if max_viande is not None and viande_count > max_viande:
            continue
        if avg_budget is not None and not within_budget_avg(cand, avg_budget, tolerance):
            continue

        return cand

    # Fallback raisonnable
    fallback = pool[:days] if len(pool) >= days else (pool + pool)[:days]

    # Vérifie fallback avec min/max viande
    if min_viande or max_viande:
        fallback = [r for r in fallback if (min_viande is None or sum(is_viande(r2) for r2 in fallback) >= min_viande) 
                                    and (max_viande is None or sum(is_viande(r2) for r2 in fallback) <= max_viande)]

    return fallback

def consolidate_shopping_list(menu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrège les ingrédients par nom et unité."""
    agg: Dict[Tuple[str, str], float] = {}
    for r in menu:
        for ing in r.get("ingredients", []):
            key = (ing["name"].strip().lower(), ing.get("unit", "").strip().lower())
            agg[key] = agg.get(key, 0.0) + float(ing.get("qty", 0.0))
    return [{"name": name, "qty": round(qty,2), "unit": unit} for (name, unit), qty in sorted(agg.items())]

def plan_menu(
    recipes: List[Dict[str, Any]],
    days: int = 7,
    min_vege: Optional[int] = 2,
    max_time: Optional[int] = None,
    avg_budget: Optional[float] = None,
    tolerance: float = 0.2,
    seed: Optional[int] = 42,
    exclude_ingredients: Optional[List[str]] = None,
    min_viande: Optional[int] = None,
    max_viande: Optional[int] = None,
    no_duplicates: bool = False,
) -> Dict[str, Any]:
    menu = select_menu(
        recipes=recipes,
        days=days,
        min_vege=min_vege,
        max_time=max_time,
        avg_budget=avg_budget,
        tolerance=tolerance,
        seed=seed,
        exclude_ingredients=exclude_ingredients,
        min_viande=min_viande,
        max_viande=max_viande,
        no_duplicates=no_duplicates,
    )
    shopping = consolidate_shopping_list(menu)
    return {"days": days, "menu": menu, "shopping_list": shopping}