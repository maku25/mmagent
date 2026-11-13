import os
from pydantic import BaseModel, Field
from typing import Optional, Literal
from google import genai
from dotenv import load_dotenv


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Post(BaseModel):
    type_post: Literal["Annonce", "Resultat", "News"] = Field(description="Catégorie de l'actualité")
    resultat_combat: Optional[Literal["Victoire", "Defaite", "Nul"]] = Field(
        None, description="Uniquement si type_post='Resultat' : indique si le combattant turc a gagné, perdu ou fait match nul."
    )
    nom_combattant: str = Field(description="Nom complet du combattant principal concerné (ex: Ibo Aslan, Tayfun Özcan)")
    surnom: Optional[str] = Field(None, description="Surnom du combattant s'il est mentionné (ex: The Last Ottoman)")
    adversaire: Optional[str] = Field(None, description="Nom de l'adversaire s'il est mentionné")
    organisation: Optional[str] = Field(None, description="L'organisation (ex: UFC, KSW, Glory, ONE Championship)")
    date_combat: Optional[str] = Field(None, description="Date de l'événement si mentionnée")
    methode_victoire: Optional[str] = Field(None, description="Méthode s'il s'agit d'un résultat (ex: KO, TKO, Soumission, Décision)")
    categorie: Optional[str] = Field(None, description="Catégorie de poids si mentionnée (ex: Poids lourds-légers, Welters)")
    score_importance: int = Field(description="Score de pertinence de 1 à 10 (10 = titre/gros KO, 5 = annonce standard, 1 = bruit)")

    titre: str = Field(description="Titre court en MAJUSCULES sans emoji (ex: 'IBO ASLAN DE RETOUR À L'UFC', 'VICTOIRE EXPÉDITIVE DE BAYSANGUR', 'FORFAIT POUR BLESSURE')")
    corps: str = Field(description="1 à 3 phrases naturelles et punchy résumant l'info. Explosif si victoire/annonce, respectueux et encourageant si défaite, informatif si news.")
    question: Optional[str] = Field(None, description="Question courte pour faire réagir les abonnés en commentaire")

def extraire_information(texte: str) -> Post:

    prompt_systeme = """
    Tu es le rédacteur en chef d'un média X (Twitter) spécialisé dans les sports de combat (MMA, Kickboxing, Boxe, Muay Thaï) suivant les combattants turcs.
    1. Extrais les informations factuelles du texte brut. Si une donnée manque, laisse null (n'invente jamais de faits).
    2. Rédige les champs éditoriaux (titre, corps, question) en français avec un style percutant, dynamique et naturel, adapté aux réseaux sociaux et au jargon du combat (octogone, cage, striking, KO, short-notice, etc.).
    3. Adapte le ton : explosif pour une victoire ou une annonce, sobre et respectueux pour une défaite, informatif pour une news.
    """

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents = f"{prompt_systeme}\n\nTexte source : {texte}",
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Post,
        ),
    )

    return Post.model_validate_json(response.text)

if __name__ == "__main__":
    texte_test = "🚨 C'est officiel ! Ibo Aslan va affronter Anton Turkalj chez les lourds-légers le 30 Mars prochain à l'UFC Atlantic City. Gros combat en perspective !"

    print("🧠...\n")
    resultat = extraire_information(texte_test)
    
    print("------")
    print(resultat.model_dump_json(indent=2))
