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

    args = p.parse_args()

    recipes = load_recipes(args.recipes)
    result = plan_menu(
        recipes,
        days=args.days,
        min_vege=args.min_vege,
        max_time=args.max_time,
        avg_budget=args.avg_budget,
        tolerance=args.tolerance,
        seed=args.seed,
    )
    save_json(result, args.output)

if __name__ == "__main__":
    main()