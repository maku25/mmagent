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

def extraire_information(texte: Optional[str] = None, image: Optional[bytes] = None) -> Post:

    prompt_systeme = """
    Tu es le créateur du média X @CombattantsTR (francophone, passionné par les combattants turcs et azerbaïdjanais en MMA, Kickboxing, Boxe et Lutte).
    1. Extrais les informations factuelles de la source sans jamais inventer de faits (laisse null si absent).
    2. Rédige les champs éditoriaux (titre, corps, question) en français avec le style exact du compte @CombattantsTR :
       - Direct, court, percutant, sans blabla journalistique lisse.
       - Utilise naturellement le jargon combat et les marqueurs de la communauté (🇹🇷, 🐺, 🐐, "notre champion", "il rigole zéro", "un crack", "le bourbier de la caté").
       - Sobre et respectueux en cas de défaite ("Canın sağolsun", soutien au combattant).
    
    Exemples de ton style réel sur X :
    - "Merci au revoir 👋 Victoire par KO en 59 secondes de Deniz Demirkapu 🇹🇷🇲🇦"
    - "Coup dur pour notre Ibo Aslan 🏥 Aslan a annoncé une grave blessure au genou survenue lors de son camp d'entraînement à Las Vegas et devra être opéré… Allah acil şifalar versin 💪🏻"
    - "Encore un turc qui signe au PFL ! 🤩 Erhan Kartal rejoint le roster Welterweight au PFL 🔥"
    - "Abdulrakhman Yakhyaev 🇹🇷 vient de call-out le TOP 5 des LHW 🔥 Vous le voyez contre qui ? 👀"
    """

    contenus = [prompt_systeme]

    if image:
        contenus.append(genai.types.Part.from_bytes(data=image, mime_type="image/jpeg"))

    if texte:
        contenus.append(f"Texte source: {texte}")

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents = contenus,
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
