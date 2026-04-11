import re

from pydantic import BaseModel, Field


class JobContext(BaseModel):
    job_title: str
    job_type: str = "emploi"
    job_level: str = "standard"

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    required_months: int = 0
    job_education_texts: list[str] = Field(default_factory=list)


class SkillMatchInput(BaseModel):
    matched_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)


class ExperienceMatchInput(BaseModel):
    total_months: int = 0


class EducationMatchInput(BaseModel):
    candidate_education_texts: list[str] = Field(default_factory=list)


class CandidateScoringInput(BaseModel):
    candidate_id: str
    candidate_name: str

    job: JobContext
    skills: SkillMatchInput
    experience: ExperienceMatchInput
    education: EducationMatchInput


RETENU_MIN = 62
A_REVOIR_MIN = 38
NO_MATCH_CAP = 35.0

WEIGHTS = {
    "standard": {"skills": 0.70, "experience": 0.20, "education": 0.10},
    "junior": {"skills": 0.65, "experience": 0.15, "education": 0.20},
    "senior": {"skills": 0.70, "experience": 0.25, "education": 0.05},
    "stage": {"skills": 0.60, "experience": 0.10, "education": 0.30},
}

EDUCATION_LEVELS = [
    ("doctorat", 5),
    ("phd", 5),
    ("docteur", 5),
    ("bac+5", 4),
    ("master", 4),
    ("mastère", 4),
    ("mastere", 4),
    ("msc", 4),
    ("mba", 4),
    ("ingénieur", 4),
    ("ingenieur", 4),
    ("bac+3", 3),
    ("licence", 3),
    ("license", 3),
    ("bachelor", 3),
    ("bac+2", 2),
    ("dut", 2),
    ("bts", 2),
    ("deug", 2),
    ("baccalauréat", 1),
    ("baccalaureat", 1),
    ("bac", 1),
]


def pick_weights(job_type: str, job_level: str) -> tuple[dict[str, float], str]:
    if job_type == "stage":
        return WEIGHTS["stage"], "stage"

    if job_level == "junior":
        return WEIGHTS["junior"], "junior"

    if job_level == "senior":
        return WEIGHTS["senior"], "senior"

    # Tous les autres cas tombent sur le mode standard
    return WEIGHTS["standard"], "standard"


def detect_edu_lvl(texts: list[str]) -> int:
    best = 0

    for text in texts:
        text = str(text).lower()

        for keyword, lvl in EDUCATION_LEVELS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text):
                best = max(best, lvl)
                break

    return best


def score_skills(
    required_skills: list[str],
    preferred_skills: list[str],
    matched_required_skills: list[str],
    matched_preferred_skills: list[str],
) -> float:
    req_count = len(required_skills)
    pref_count = len(preferred_skills)
    matched_req = len(matched_required_skills)
    matched_pref = len(matched_preferred_skills)

    # Aucun signal exploitable côté compétences
    if req_count == 0 and pref_count == 0:
        return 50.0

    # S'il n'y a pas d'obligatoires, on note seulement sur les appréciées
    if req_count == 0:
        return round((matched_pref / pref_count) * 60, 2)

    # Base principale sur les compétences obligatoires
    score = (matched_req / req_count) * 85

    if pref_count > 0:
        # Petit bonus sur les compétences appréciées
        pref_bonus = (matched_pref / pref_count) * 15

        # Évite qu'un bonus masque une absence totale sur les obligatoires
        if matched_req == 0:
            pref_bonus = min(pref_bonus, 5.0)

        score += pref_bonus

    return min(round(score, 2), 100.0)


def score_experience(total_months: int, required_months: int) -> float:
    # Si aucune durée n'est demandée, on applique une règle simple
    if required_months <= 0:
        return min(round(total_months * 2.5, 2), 100.0)

    # Sinon on compare l'expérience du candidat à celle demandée
    ratio = min(total_months / required_months, 1.25)
    return min(round(ratio * 100, 2), 100.0)


def score_edu(cand_lvl: int, req_lvl: int) -> float:
    if req_lvl == 0:
        # Aucun niveau clairement détecté dans le poste
        return 70.0

    if cand_lvl == 0:
        # Aucun niveau détecté chez le candidat
        return 35.0

    if cand_lvl >= req_lvl:
        score = 90.0
    elif cand_lvl == req_lvl - 1:
        # Cas légèrement en dessous du niveau attendu
        score = 68.0
    else:
        score = 45.0

    return round(score, 2)


def score_total(
    skill_score: float,
    exp_score: float,
    edu_score: float,
    weights: dict[str, float],
) -> float:
    total = (
        skill_score * weights["skills"]
        + exp_score * weights["experience"]
        + edu_score * weights["education"]
    )

    return round(total, 2)


def apply_safety_cap(
    total: float, required_skills: list[str], matched_required_skills: list[str]
) -> float:
    # Empêche un bon score global si rien n'a été retrouvé sur les obligatoires
    if required_skills and not matched_required_skills:
        return min(total, NO_MATCH_CAP)

    return total


def classify(global_score: float) -> str:
    if global_score >= RETENU_MIN:
        return "RETENU"

    if global_score >= A_REVOIR_MIN:
        return "A_REVOIR"

    return "REJETE"


def build_flags(decision: str, missing_required_skills: list[str]) -> dict:
    send = decision in {"RETENU", "A_REVOIR"}

    return {
        "envoyer_agent3": send,
        "competences_cibles_agent3": missing_required_skills if send else [],
    }


def compute_scoring(data: CandidateScoringInput) -> dict:
    job = data.job
    skills = data.skills
    exp = data.experience
    edu = data.education

    # S'il manque complètement le résultat sur les compétences obligatoires,
    # on considère que l'évaluation n'est pas exploitable
    if job.required_skills:
        no_matching_output = (
            not skills.matched_required_skills and not skills.missing_required_skills
        )

        if no_matching_output:
            return {
                "erreur": True,
                "raison": "aucun résultat de matching reçu pour les compétences obligatoires",
                "decision": "NON_EVALUE",
            }

    weights, mode = pick_weights(job.job_type, job.job_level)

    skill_score = score_skills(
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        matched_required_skills=skills.matched_required_skills,
        matched_preferred_skills=skills.matched_preferred_skills,
    )

    exp_score = score_experience(
        total_months=exp.total_months,
        required_months=job.required_months,
    )

    cand_lvl = detect_edu_lvl(edu.candidate_education_texts)
    req_lvl = detect_edu_lvl(job.job_education_texts)
    edu_score = score_edu(cand_lvl, req_lvl)

    global_score = score_total(skill_score, exp_score, edu_score, weights)
    global_score = apply_safety_cap(
        global_score,
        job.required_skills,
        skills.matched_required_skills,
    )

    decision = classify(global_score)
    flags = build_flags(decision, skills.missing_required_skills)

    return {
        "candidat_id": data.candidate_id,
        "candidat_nom": data.candidate_name,
        "poste_titre": job.job_title,
        "score_global": global_score,
        "decision": decision,
        "scores_detail": {
            "competences": {
                "score": skill_score,
                "poids": weights["skills"],
                "match_obligatoires": skills.matched_required_skills,
                "match_appreciees": skills.matched_preferred_skills,
                "lacunes_obligatoires": skills.missing_required_skills,
            },
            "experience": {
                "score": exp_score,
                "poids": weights["experience"],
                "total_mois": exp.total_months,
                "requis_mois": job.required_months,
            },
            "formation": {
                "score": edu_score,
                "poids": weights["education"],
                "niveau_candidat": cand_lvl,
                "niveau_requis": req_lvl,
            },
            "mode_poids": mode,
        },
        "flags": flags,
    }
