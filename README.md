### MealMaker — Planificateur de menus

Objectif: Générer un menu de N jours à partir d'un catalogue de recettes et produire une liste de courses agrégée.

#### Installation
- Python 3.11+
- `pip install -r requirements.txt`

### Objectif
- Faire evoluer le projet sur le principe de l'integration continue (une feature + tests associé)
    Filtres supplémentaires
        --min-fish, --max-meat: contrainte sur certains tags (ex: “poisson”, “viande”).
        --exclude-ingredients: exclure certains ingrédients (allergènes).
        --no-duplicates: éviter les doublons exacts de recettes dans la semaine.
        Contrainte sur budget total hebdo --max-weekly-budget.

#### Utilisation
```bash
python -m mealmaker.cli --recipes data/recipes.sample.json --days 7 --min-vege 2 --max-time 30 --avg-budget 2.5 --output plan.json


python -m mealmaker.cli --recipes data/recipes.sample.json --days 7 --min-vege 2 --max-time 30 --avg-budget 2.5 --exclude-ingredients lait oeuf --output plan.json #Ligne Valentin