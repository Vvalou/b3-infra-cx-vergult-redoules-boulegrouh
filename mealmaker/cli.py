import argparse
from .io import load_recipes, save_json
from .core import plan_menu


def main():
    p = argparse.ArgumentParser(prog="mealmaker")
    p.add_argument("--recipes", default="data/recipes.sample.json")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--min-vege", type=int, default=2)
    p.add_argument("--max-time", type=int, default=None)
    p.add_argument("--avg-budget", type=float, default=None)
    p.add_argument("--tolerance", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default=None, help="Chemin pour sauvegarder le JSON")

    # Options supplémentaires
    p.add_argument("--exclude-ingredients", nargs="+", default=[], help="Liste d'ingrédients à exclure")  # Allergènes
    p.add_argument("--no-duplicates", action="store_true", help="Éviter les doublons exacts de recettes dans la semaine")  # Anti-doublons
    p.add_argument("--min-viande", type=float, default=None,
                   help="Minimum de plats viande (arrondi à l’entier supérieur si décimal).")
    p.add_argument("--max-viande", type=float, default=None,
                   help="Maximum de plats viande (arrondi à l’entier inférieur si décimal).")

    args = p.parse_args()

    if args.days <= 0:
        p.error("--days doit être > 0")

    recipes = load_recipes(args.recipes)
    result = plan_menu(
        recipes=recipes,
        days=args.days,
        min_vege=args.min_vege,
        max_time=args.max_time,
        avg_budget=args.avg_budget,
        tolerance=args.tolerance,
        seed=args.seed,
        exclude_ingredients=args.exclude_ingredients,  # Allergènes
        no_duplicates=args.no_duplicates,              # Anti-doublons
        min_viande=args.min_viande,
        max_viande=args.max_viande,
    )
    save_json(result, args.output)


if __name__ == "__main__":
    main()
