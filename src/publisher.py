import json
from pathlib import Path

from agent import Post, extraire_information

def charger_templates() -> dict:
    chemin_templates = Path(__file__).parent.parent / "prompts" / "templates.json"
    with open(chemin_templates, "r", encoding="utf-8") as f:
        return json.load(f)

def generer_post(data: Post) -> str:

    templates = charger_templates()

    if data.type_post == "Resultat":
        if data.resultat_combat == "Defaite":
            cle_template = "Resultat_Defaite"
        else:
            cle_template = "Resultat_Victoire"
    else:
        cle_template = data.type_post

    type_template = templates.get(cle_template)

    if not type_template:
        raise ValueError(f"Template inconnu pour le type : {data.type_post}")


    orga_propre = (data.organisation or "CombatSports").replace(" ", "")

    donnees_formatage = {
        "nom_combattant": data.nom_combattant,
        "surnom": data.surnom or "",
        "adversaire": data.adversaire or "À déterminer",
        "organisation": orga_propre,
        "date_combat": data.date_combat or "Date à venir",
        "methode_victoire": data.methode_victoire or "décision",
        "categorie": data.categorie or "Poids non précisé",
        "titre": data.titre,
        "corps": data.corps,
        "question": data.question or ""
    }
    
    post_final = type_template.format(**donnees_formatage)
    return post_final

if __name__ == "__main__":
    texte_test = "Quelle performance ! Ibo Aslan vient de mettre KO Anton Turkalj dès le premier round avec un crochet gauche monstrueux à l'UFC Atlantic City !"    

    donnees_extraites = extraire_information(texte_test)
    post = generer_post(donnees_extraites)
    print(post)
    