import json
from collections import defaultdict

# Charger le fichier brut
with open("products.json", "r", encoding="utf-8") as f:
    produits = json.load(f)

# Grouper les produits par catégorie
categories = defaultdict(list)
for produit in produits:
    cat = produit.get("category", "inconnu").strip().lower()
    categories[cat].append(produit)

# Convertir en dictionnaire ordonné par nom de catégorie
categories_ordonnees = dict(sorted(categories.items()))

# Sauvegarder le nouveau fichier structuré
with open("products_by_category.json", "w", encoding="utf-8") as f:
    json.dump(categories_ordonnees, f, ensure_ascii=False, indent=2)

print("✅ Les produits ont été réorganisés par catégorie.")
