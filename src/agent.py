import os
from pydantic import BaseModel, Field
from typing import Optional, Literal
from google import genai
from dotenv import load_dotenv


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class Post(BaseModel):
    type_post: Literal["Annonce", "Resultat", "News"] = Field(description="Catégorie de l'actualité")
    nom_combattant: str = Field(description="Nom complet du combattant principal concerné (ex: Ibo Aslan, Tayfun Özcan)")
    surnom: Optional[str] = Field(None, description="Surnom du combattant s'il est mentionné (ex: The Last Ottoman)")
    adversaire: Optional[str] = Field(None, description="Nom de l'adversaire s'il est mentionné")
    organisation: Optional[str] = Field(None, description="L'organisation (ex: UFC, KSW, Glory, ONE Championship)")
    date_combat: Optional[str] = Field(None, description="Date de l'événement si mentionnée")
    methode_victoire: Optional[str] = Field(None, description="Méthode s'il s'agit d'un résultat (ex: KO, TKO, Soumission, Décision)")
    categorie: Optional[str] = Field(None, description="Catégorie de poids si mentionnée (ex: Poids lourds-légers, Welters)")
    score_importance: int = Field(description="Score de pertinence de 1 à 10 (10 = titre/gros KO, 5 = annonce standard, 1 = bruit)")

def extraire_information(texte: str) -> Post:

    prompt_systeme = """
    Tu es l'agent IA d'un média spécialisé dans les sports de combat.
    Ton rôle est d'extraire les informations factuelles d'un texte brut.
    Si une information n'est pas présente dans le texte, laisse la valeur à null. N'invente rien.
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
