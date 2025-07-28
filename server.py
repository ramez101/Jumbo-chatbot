from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
import json
import re
import unicodedata
from fuzzywuzzy import fuzz
import os


app = Flask(__name__)
CORS(app)

client = Together(api_key="tgp_v1_3cdZMXb--n2gnr2ZXkeSyiCWAbx-il8zun2mhsbw0qA")

with open("products_by_category.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

produits = []
for liste in raw.values():
    produits.extend(liste)

toutes_les_marques = {p.get("brand", "").strip().lower() for p in produits if p.get("brand")}

def nettoyer(texte):
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^\w\s]', ' ', texte.lower()).strip()

def extraire_prix(prix_str):
    try:
        texte = prix_str.replace(" ", "").replace(" ", "").strip()
        match = re.search(r'[\d.,]+', texte)
        if not match:
            return 0.0
        nombre = match.group()
        if ',' in nombre and '.' not in nombre:
            nombre = nombre.replace(',', '.')
        else:
            nombre = nombre.replace(',', '')
        return float(nombre)
    except:
        return 0.0

def extraire_prix_du_message(message):
    prix_min = prix_max = None
    message = message.lower().replace(',', '').replace('.', '')

    try:
        match_entre = re.search(r"(entre|de)\s+(\d+)\s+(et|à)\s+(\d+)", message)
        if match_entre:
            prix_min = float(match_entre.group(2))
            prix_max = float(match_entre.group(4))
            return prix_min, prix_max

        match_min = re.search(r"(?:prix\s*[>]\s*|plus\s+de\s+|à\s+partir\s+de\s+)(\d+)", message)
        if match_min:
            prix_min = float(match_min.group(1))

        match_max = re.search(r"(?:prix\s*[<]\s*|moins\s+de\s+)(\d+)", message)
        if match_max:
            prix_max = float(match_max.group(1))

    except:
        pass

    return prix_min, prix_max


def filtrer_produits(message, prix_min=None, prix_max=None, categorie=None):
    produits_par_marque = []
    produits_affines = []
    produits_detail = []
    message_clean = nettoyer(message)
    keywords = message_clean.split()

    # ✅ Détection stricte d'une marque dans le message
    marque_detectee = next(
        (marque for marque in toutes_les_marques
         if re.search(rf"\b{re.escape(marque)}\b", message_clean)),
        None
    )

    for p in produits:
        prix = extraire_prix(p.get("price", "0"))
        prix_original = p.get("price", "").strip()
        prix_match = (prix_min is None or prix >= prix_min) and (prix_max is None or prix <= prix_max)

        texte_brand = nettoyer(p.get('brand', ''))
        texte_detail = nettoyer(f" {p.get('category', '')}")

        # ✅ Si une marque est détectée → filtrer uniquement cette marque
        if marque_detectee and texte_brand != marque_detectee:
            continue

        score_brand = sum(1 for kw in keywords if kw in texte_brand)
        score_detail = sum(1 for kw in keywords if kw in texte_detail)

        similarity = fuzz.partial_ratio(message_clean, texte_detail)

        if prix_match and (score_brand > 0 or score_detail > 0 or similarity >= 70):
            p["prix_numerique"] = prix
            p["prix_original"] = prix_original

            if score_brand > 0:
                produits_par_marque.append((score_brand, -prix, p))
            else:
                produits_detail.append((score_detail + similarity / 100, -prix, p))

    # ✅ Tri et retour des meilleurs résultats
    produits_par_marque.sort(reverse=True, key=lambda x: (x[0], x[1]))
    produits_detail.sort(reverse=True, key=lambda x: (x[0], x[1]))

    if produits_par_marque:
        return [p for _, _, p in produits_par_marque[:min(6, len(produits_par_marque))]]
    elif produits_detail:
        return [p for _, _, p in produits_detail[:min(6, len(produits_detail))]]
    else:
        return []


def generer_cartes_html(produits_trouves):
    if not produits_trouves:
        return ""
    
    html = '''
    <div class="carousel-container">
        <button class="carousel-button prev" onclick="scrollCarousel(-1)">&#10094;</button>
        <div class="carousel" id="carousel">
    '''
    for p in produits_trouves:
        html += f"""
        <div class="carousel-item">
            <img src="{p['image_url']}" alt="{p['title']}">
            <h3>{p['title']}</h3>
            <div class="price">{p['prix_original']}</div>
            <p class="product-availability">Disponibilité : <strong>{p['availability']}</strong></p>
            <a class="product-link" href="{p['product_url']}" target="_blank">View Product</a>
        </div>
        """
    html += '''
        </div>
        <button class="carousel-button next" onclick="scrollCarousel(1)">&#10095;</button>
    </div>
    '''
    return html

@app.route("/")
def index():
    return "✅ The Flask API is up and running! Use POST /api/chat or /api/brands."

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message", "")
        categorie = data.get("categorie")

        prix_min = data.get("prix_min")
        prix_max = data.get("prix_max")

        print(f"[INPUT] Message: {message}")
        print(f"[INPUT] Categorie: {categorie}, Prix min: {prix_min}, Prix max: {prix_max}")

        if prix_min is None and prix_max is None:
            prix_min, prix_max = extraire_prix_du_message(message)
            print(f"[PARSED] Extracted price range: min={prix_min}, max={prix_max}")
        else:
            try:
                prix_min = float(prix_min) if prix_min is not None else None
                prix_max = float(prix_max) if prix_max is not None else None
            except ValueError:
                prix_min = prix_max = None

        produits_filtres = filtrer_produits(message, prix_min, prix_max, categorie)
        print(f"[FILTER] {len(produits_filtres)} products matched.")

        produits_trouves = produits_filtres[:6]

        prompt = f"""
L'utilisateur a demandé : "{message}"

Voici une liste de produits disponibles (titre, prix, catégorie) :
{produits_filtres}

Ta tâche, en tant qu'expert e-commerce, est de :
- Comprendre la demande de l'utilisateur
- Répondre avec une phrase naturelle, engageante et claire
- Introduire la liste avec une phrase personnalisée
- NE PAS répondre par une liste, seulement une phrase introductive.
"""

        try:
            response_stream = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            bot_reply = ""
            for chunk in response_stream:
                if hasattr(chunk, "choices") and chunk.choices[0].delta:
                    content_piece = chunk.choices[0].delta.content
                    if content_piece:
                        bot_reply += content_piece
        except Exception as e:
            bot_reply = f"Erreur modèle : {str(e)}"

        html_reponse = generer_cartes_html(produits_trouves)

        return jsonify({
            "reply": f"{bot_reply}\n{html_reponse}",
            "products": produits_trouves,
            "filters": {
                "prix_min": prix_min,
                "prix_max": prix_max,
                "categorie": categorie,
                "message": message
            }
        })

    except Exception as e:
        return jsonify({"reply": f"Erreur interne : {str(e)}"}), 500


@app.route("/api/brands", methods=["POST"])
def get_brands():
    data = request.get_json()
    message = data.get("message", "")
    message_clean = nettoyer(message)
    print(f"[BRAND DETECTION] Cleaned message: {message_clean}")

    # ✅ Correction : détection stricte des marques dans le message
    marque_deja_mentionnee = any(
        re.search(rf"\b{re.escape(marque)}\b", message_clean)
        for marque in toutes_les_marques
    )

    if marque_deja_mentionnee:
        print("[BRAND DETECTION] Brand already in message.")
        return jsonify({"brands": []})

    toutes_les_categories = list({nettoyer(p.get("category", "")) for p in produits if p.get("category")})
    similarites = [(fuzz.token_set_ratio(message_clean, cat), cat) for cat in toutes_les_categories]

    max_score = max([s for s, _ in similarites], default=0)
    seuil = max(85, max_score - 5)
    categories_trouvees = {cat for score, cat in similarites if score >= seuil}

    marques_trouvees = set()
    for p in produits:
        cat = nettoyer(p.get("category", ""))
        if cat in categories_trouvees:
            brand = p.get("brand", "").strip()
            if brand:
                marques_trouvees.add(brand)

    print(f"[BRANDS FOUND] {marques_trouvees}")
    return jsonify({"brands": list(marques_trouvees)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # use Render's PORT or default to 5000
    app.run(host="0.0.0.0", port=port, debug=False)
