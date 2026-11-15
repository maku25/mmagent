import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

from agent import extraire_information
from publisher import generer_post

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

DOSSIER_DATA = Path(__file__).parent.parent / "data"
CHEMIN_WATCHLIST = DOSSIER_DATA / "watchlist.json"
CHEMIN_SEEN = DOSSIER_DATA / "seen_urls.json"

SEUIL_IMPORTANCE = 5 
JOURS_RECHERCHE = 30

def charger_watchlist() -> list[dict]:
    with open(CHEMIN_WATCHLIST, "r", encoding="utf-8") as f:
        return json.load(f).get("combattants", [])

def charger_urls_vues() -> set[str]:
    if not CHEMIN_SEEN.exists():
        return set()
    with open(CHEMIN_SEEN, "r", encoding="utf-8") as f:
        return set(json.load(f))

def sauvegarder_urls_vues(urls: set[str]):
    with open(CHEMIN_SEEN, "w", encoding="utf-8") as f:
        json.dump(list(urls), f, indent=2)

def chercher_actus_tavily(requete: str) -> list[dict]:
    """Interroge l'API Tavily et retourne les 3 articles récents les plus pertinents."""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY est manquant dans le fichier .env")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": requete,
        "topic": "news",
        "days": JOURS_RECHERCHE,
        "search_depth": "basic",
        "max_results": 3
    }

    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json().get("results", [])

def scanner_combattant(combattant: dict, urls_vues: set[str]) -> list[str]:
    """Scanne les actus d'un combattant via Tavily, fusionne les sources et génère 1 post consolidé."""
    try:
        articles = chercher_actus_tavily(combattant["requete"])
    except Exception as e:
        print(f"Erreur Tavily pour {combattant['nom']} : {e}")
        return []

    nouveaux_articles = [
        a for a in articles
        if a.get("url") and a.get("url") not in urls_vues
    ]

    if not nouveaux_articles:
        return []

    print(f"{len(nouveaux_articles)} nouvelle(s) source(s) détectée(s) pour {combattant['nom']}")

    blocs_sources = []
    liens_sources = []

    for i, article in enumerate(nouveaux_articles, 1):
        lien = article["url"]
        titre = article.get("title", "")
        date_pub = article.get("published_date", "Date inconnue")
        extrait = article.get("content", "")

        blocs_sources.append(
            f"--- SOURCE {i} ---\n"
            f"Titre : {titre}\n"
            f"Date : {date_pub}\n"
            f"Extrait : {extrait}\n"
        )
        liens_sources.append(lien)

    texte_brut = (
        f"Combattant ciblé : {combattant['nom']} ({combattant['organisation']})\n"
        f"Voici {len(nouveaux_articles)} sources récentes trouvées sur le web. "
        f"Croise ces sources pour extraire l'actualité principale la plus complète concernant {combattant['nom']} :\n\n"
        + "\n".join(blocs_sources)
    )

    try:
        donnees = extraire_information(texte=texte_brut)

        for lien in liens_sources:
            urls_vues.add(lien)

        if donnees.score_importance >= SEUIL_IMPORTANCE:
            post = generer_post(donnees)
            sources_formatees = "\n".join(f"🔗 {u}" for u in liens_sources)
            post_complet = f"{post}\n\nSources :\n{sources_formatees}"
            print(f"Post consolidé validé (Pertinence : {donnees.score_importance}/10)")
            return [post_complet]
        else:
            print(f"Ignoré (Pertinence trop faible : {donnees.score_importance}/10)")
            return []

    except Exception as e:
        print(f"Erreur analyse Gemini sur {combattant['nom']} : {e}")
        return []

def lancer_veille() -> list[str]:
    combattants = charger_watchlist()
    urls_vues = charger_urls_vues()
    tous_les_posts = []

    print("Démarrage du scan via Tavily...")
    for c in combattants:
        posts = scanner_combattant(c, urls_vues)
        tous_les_posts.extend(posts)

    sauvegarder_urls_vues(urls_vues)
    print(f"Scan terminé : {len(tous_les_posts)} post généré.")
    return tous_les_posts

if __name__ == "__main__":
    resultats = lancer_veille()
    for p in resultats:
        print("\n" + "=" * 40 + "\n")
        print(p)
