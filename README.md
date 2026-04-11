# Etape 3 - Scoring & Decision

HOLA AMIGOS

De mon cote, j'ai travaille sur l'etape 3 de l'Agent 2, donc la partie scoring et prise de decision apres le matching CV <-> offre.

Le but ici est simple :

- sortir un score global
- sortir une decision
- garder un detail par critere
- envoyer des flags utiles pour la suite

Je me suis base sur le role naturel d'une etape "Scoring & Decision", sur la slide de l'etape 3, et sur l'exemple JSON qu'on avait deja dans l'etape 4 du rapport final.

Petit point technique : j'ai utilise Pydantic surtout pour garder une structure d'entree claire pour le poste, les competences, l'experience et la formation.

Donc j'ai organise l'etape 3 autour de 4 taches.

---

## 1. Attribution des poids selon le poste

La premiere chose que fait l'etape 3, c'est choisir un profil de ponderation selon le type ou le niveau du poste.

J'ai garde 4 profils :

- `standard`
- `junior`
- `senior`
- `stage`

L'idee est la suivante :

- en `standard`, les competences restent le critere principal
- en `junior`, la formation compte un peu plus
- en `senior`, l'experience compte plus
- en `stage`, la formation et le potentiel comptent davantage

Le mode `standard` couvre aussi les postes intermediaires.

---

## 2. Calcul des scores par dimension

J'ai separe le scoring en 3 dimensions :

- competences
- experience
- formation

### Competences

Le score competences repose surtout sur :

- les competences obligatoires retrouvees
- les competences appreciees retrouvees
- les competences obligatoires manquantes

Les obligatoires pesent le plus. Les appreciees donnent un bonus, mais ce bonus ne doit pas compenser une absence sur les obligatoires.

Exemple simple :

- l'offre demande Python, SQL, Docker
- le candidat a Python et SQL
- il lui manque Docker

Donc la base du score competences part surtout de 2 obligatoires retrouves sur 3.

### Experience

Dans cette version, l'experience est notee de maniere simple a partir des mois :

- experience totale du candidat
- experience demandee par le poste

Si le poste precise une duree, on compare les mois du candidat a cette duree.
Sinon on applique une regle simple basee sur le total de mois.

Je n'ai pas ajoute ici une logique plus avancee sur la pertinence reelle de l'experience, parce que cela dependra de ce que l'etape 2 pourra produire plus tard.

### Formation

Pour la formation, j'ai utilise une logique simple de detection du niveau a partir du texte :

- doctorat
- bac+5 / master / ingenieur / msc / mba
- bac+3 / licence / bachelor
- bac+2 / dut / bts
- bac

Ensuite on compare :

- le niveau detecte cote candidat
- le niveau detecte cote poste

En gros :

- niveau atteint ou depasse -> bon score
- legerement en dessous -> score moyen
- plus bas -> score plus faible
- rien detecte -> score faible ou neutre selon le cas

Exemple simple :

- candidat : Licence en informatique -> niveau 3
- poste : Master / Bac+5 -> niveau 4

Donc ici on est sur une logique de niveau, pas encore sur une logique fine de specialisation.

---

## 3. Calcul du score global et decision

Une fois les 3 sous-scores calcules, on applique les poids du poste pour produire un score global.

Ensuite ce score global est transforme en decision selon des seuils simples :

- `RETENU`
- `A_REVOIR`
- `REJETE`

J'ai aussi ajoute un garde-fou :

si le poste a des competences obligatoires mais qu'aucune n'a ete retrouvee, alors le score global est plafonne.

J'ai aussi rendu la decision `RETENU` un peu plus stricte :

- pour un poste standard, il faut quand meme une couverture minimale des obligatoires
- pour un stage, cette regle est plus souple

---

## 4. Generation des flags pour la suite

Enfin, l'etape 3 genere les flags utiles pour la suite.

L'idee actuelle est simple :

- si le candidat est `RETENU` ou `A_REVOIR`, on peut le transmettre a l'etape suivante
- si besoin, on transmet aussi les competences obligatoires manquantes comme cibles prioritaires

---

## Comment j'ai teste cette logique

J'ai essaye plusieurs cas simules :

- un candidat fort
- un candidat borderline
- un candidat faible

Le but etait surtout de verifier que :

- le scoring reste coherent
- la decision reste lisible
- les cas faibles ne passent pas artificiellement
- les cas moyens tombent plutot dans `A_REVOIR`
- les cas forts montent naturellement en `RETENU`

---

## Important : cette etape depend forcement des sorties des etapes precedentes

Cette etape depend completement de ce que l'etape 1 et surtout l'etape 2 vont reellement fournir.

Donc ici, j'ai surtout essaye de poser une logique metier claire avec des elements simples :

- competences obligatoires et appreciees
- ce qui a ete matche ou non
- le nombre de mois d'experience
- les textes de formation

Si plus tard vous fournissez des signaux plus riches, on pourra raffiner le scoring.

---

## Exemple simple de test

Pour verifier que la logique tenait la route, j'ai aussi essaye un cas simule un peu plus limite.

### Entree simulee

```json
{
  "candidate_id": "C02",
  "candidate_name": "Sara El Amrani",
  "job": {
    "job_title": "Analyste de donnees",
    "job_type": "emploi",
    "job_level": "standard",
    "required_skills": ["Python", "SQL", "Power BI", "Excel"],
    "preferred_skills": [],
    "required_months": 24,
    "job_education_texts": ["Bac+5 en informatique, data ou equivalent"]
  },
  "skills": {
    "matched_required_skills": ["Python", "SQL", "Excel"],
    "matched_preferred_skills": [],
    "missing_required_skills": ["Power BI"]
  },
  "experience": {
    "total_months": 15
  },
  "education": {
    "candidate_education_texts": ["Licence en economie et gestion"]
  }
}
```

### Resultat obtenu

```json
{
  "candidat_id": "C02",
  "candidat_nom": "Sara El Amrani",
  "poste_titre": "Analyste de donnees",
  "score_global": 63.92,
  "decision": "RETENU",
  "scores_detail": {
    "competences": {
      "score": 63.75,
      "poids": 0.7,
      "match_obligatoires": ["Python", "SQL", "Excel"],
      "match_appreciees": [],
      "lacunes_obligatoires": ["Power BI"]
    },
    "experience": {
      "score": 62.5,
      "poids": 0.2,
      "total_mois": 15,
      "requis_mois": 24
    },
    "formation": {
      "score": 68.0,
      "poids": 0.1,
      "niveau_candidat": 3,
      "niveau_requis": 4
    },
    "mode_poids": "standard"
  },
  "flags": {
    "envoyer_agent3": true,
    "competences_cibles_agent3": ["Power BI"]
  }
}
```

### Lecture rapide du resultat

Dans ce cas :

- il manque encore une competence obligatoire
- son experience est en dessous de ce qui est demande
- sa formation est un peu en dessous du niveau attendu

Donc ce n'est pas un profil tres fort, mais il peut quand meme passer en `RETENU`.

| Partie | Resultat |
|---|---|
| Competences | `63.75` |
| Experience | `62.5` |
| Formation | `68.0` |
| Score global | `63.92` |
| Decision | `RETENU` |

---

## Limites actuelles du scoring

A ce stade, cette logique reste simple, donc il y a quelques limites a garder en tete :

- le scoring depend completement des sorties des etapes 1 et 2
- l'experience repose surtout sur le nombre de mois
- la formation repose sur des mots-cles et une logique par paliers
- les poids sont des choix metier simples pour une V1
- certains intitules comme `entry level`, `intermediaire`, `stagiaire`, `internship`, etc. doivent etre bien normalises avant cette etape
- si les competences obligatoires existent mais que le matching n'est pas fourni, on retourne `NON_EVALUE`

Donc l'objectif ici n'est pas d'avoir un scoring parfait, mais une base lisible et ajustable.

---

## En resume

De mon cote, l'etape 3 est pensee comme :

1. choix des poids selon le poste
2. calcul des scores competences / experience / formation
3. calcul du score global + decision
4. generation des flags pour la suite

Si, de votre cote, vous avez deja une idee plus precise du format final de sortie de l'etape 2, je pourrai ajuster le scoring en consequence.

