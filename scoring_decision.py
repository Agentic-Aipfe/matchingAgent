SEUIL_RETENU = 62
SEUIL_A_REVOIR = 38


# Pondération métier appliquée au score sémantique selon le contexte du poste.
POIDS = {
    "standard": {"competences": 0.70, "experience": 0.20, "formation": 0.10},
    "junior": {"competences": 0.65, "experience": 0.15, "formation": 0.20},
    "senior": {"competences": 0.70, "experience": 0.25, "formation": 0.05},
    "stage": {"competences": 0.60, "experience": 0.10, "formation": 0.30},
}


def score_sur_100(valeur: float) -> float:
    return round(valeur * 100, 2)


# Score sémantique global: moyenne simple des trois similarités.
def calculer_score(
    similarite_competences: float,
    similarite_experience: float,
    similarite_formation: float,
) -> dict:
    moyenne = (
        similarite_competences
        + similarite_experience
        + similarite_formation
    ) / 3

    return {
        "competences": score_sur_100(similarite_competences),
        "experience": score_sur_100(similarite_experience),
        "formation": score_sur_100(similarite_formation),
        "score_semantique": score_sur_100(moyenne),
    }


# Choix du profil métier selon le type et le niveau du poste.
def choisir_poids(
    type_poste: str = "emploi",
    niveau_poste: str = "standard",
) -> tuple[dict[str, float], str]:
    if type_poste == "stage":
        return POIDS["stage"], "stage"

    if niveau_poste == "junior":
        return POIDS["junior"], "junior"

    if niveau_poste == "senior":
        return POIDS["senior"], "senior"

    return POIDS["standard"], "standard"


# Score final pondéré: il traduit le score sémantique en lecture métier.
def calculer_score_pondere(
    scores: dict[str, float],
    poids: dict[str, float],
) -> float:
    total = (
        scores["competences"] * poids["competences"]
        + scores["experience"] * poids["experience"]
        + scores["formation"] * poids["formation"]
    )
    return round(total, 2)


def calculer_decision(score: float) -> str:
    if score >= SEUIL_RETENU:
        return "RETENU"

    if score >= SEUIL_A_REVOIR:
        return "A_REVOIR"

    return "REJETE"


# Flags simples envoyés à l'orchestrateur pour la suite du pipeline.
def construire_flags(decision: str, lacunes: list[str]) -> dict:
    envoyer = decision in {"RETENU", "A_REVOIR"}

    return {
        "envoyer_agent3": envoyer,
        "competences_cibles_agent3": lacunes if envoyer else [],
    }


# Point d'entrée unique du fichier fusionné:
# 1. lit les similarités déjà calculées par le matching
# 2. calcule le score sémantique
# 3. applique la pondération métier
# 4. produit la décision finale
def calculer_resultat(
    donnees: dict,
    contexte_poste: dict | None = None,
) -> dict:
    contexte_poste = contexte_poste or {}

    competences = donnees["skills"]
    experience = donnees["experience"]
    formation = donnees["education"]

    scores = calculer_score(
        similarite_competences=competences["skill_similarity_score"],
        similarite_experience=experience["similarity_score"],
        similarite_formation=formation["similarity_score"],
    )

    poids, mode = choisir_poids(
        type_poste=contexte_poste.get("job_type", "emploi"),
        niveau_poste=contexte_poste.get("job_level", "standard"),
    )

    score_final = calculer_score_pondere(scores, poids)
    decision = calculer_decision(score_final)
    lacunes = competences["missing_required_skills"]
    flags = construire_flags(decision, lacunes)

    return {
        "candidat_id": donnees["candidate_id"],
        "candidat_nom": donnees["candidate_name"],
        "poste_titre": donnees["job_title"],
        "score_semantique": scores["score_semantique"],
        "score": score_final,
        "mode_poids": mode,
        "decision": decision,
        "details": {
            "competences": {
                "score": scores["competences"],
                "match": (
                    competences["matched_required_skills"]
                    + competences["matched_preferred_skills"]
                ),
                "lacunes": lacunes,
            },
            "experience": {
                "score": scores["experience"],
            },
            "formation": {
                "score": scores["formation"],
            },
        },
        "flags": flags,
    }
