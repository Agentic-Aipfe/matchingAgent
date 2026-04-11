# Etape 3 - Scoring & Decision

HOLA AMIGOS

De mon cote, j'ai travaille sur l'etape 3 de l'Agent 2, c'est-a-dire la partie scoring et prise de decision apres le matching CV <-> offre.

L'idee ici est de poser une logique simple pour transformer les resultats du matching en :

- un score global
- une decision
- des details par critere
- des flags pour la suite

Je suis parti de ce qu'une etape "Scoring & Decision" doit naturellement faire, de la slide de l'etape 3, et aussi de l'exemple JSON qu'on avait deja dans l'etape 4 du rapport final.

Petit point technique : j'ai utilise Pydantic dans le fichier surtout pour structurer les donnees d'entree de maniere claire.

Concretement, ca me permet de definir proprement :

- les infos du poste
- les infos de matching des competences
- l'experience
- la formation

L'idee ici n'est pas de compliquer le projet, mais juste d'avoir une base lisible et propre avant de lancer le scoring.

Donc j'ai structure l'etape 3 autour de 4 taches.

---

## 1. Attribution des poids selon le poste

La premiere chose que fait l'etape 3, c'est choisir un profil de ponderation selon le type ou le niveau du poste.

J'ai garde 4 profils simples :

- `standard`
- `junior`
- `senior`
- `stage`

L'idee derriere ca est assez naturelle :

- pour un poste standard, les competences restent le critere principal (ca couvre aussi les postes intermediaires)
- pour un junior, la formation compte un peu plus
- pour un senior, l'experience compte plus
- pour un stage, la formation et le potentiel comptent davantage

Donc avant meme de calculer le score, on decide avec quels poids on va lire le profil du candidat.

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

Dans la logique actuelle :

- les competences obligatoires pesent le plus
- les competences appreciees donnent un bonus
- mais ce bonus ne doit pas compenser totalement une absence sur les obligatoires

Exemple simple :

- l'offre demande comme competences obligatoires : Python, SQL, Docker
- le candidat a : Python et SQL
- il lui manque : Docker

Donc les competences obligatoires retrouvees sont 2 sur 3, et la base du score competences part de la.

Si le candidat a aussi une competence appreciee retrouvee, elle peut ajouter un petit bonus, mais elle ne remplace pas une competence obligatoire manquante.

Donc si un candidat n'a rien sur les obligatoires, il ne peut pas etre sauve uniquement par des competences "bonus".

### Experience

Pour l'instant, dans cette version au moins, l'experience est notee de maniere simple a partir des mois :

- experience totale du candidat
- experience demandee par le poste

Si le poste precise une duree attendue, on compare les mois du candidat a cette duree.
Si aucune duree n'est precisee, on utilise une regle simple basee sur le total de mois.

Je n'ai pas ajoute ici une logique plus avancee pour savoir si l'experience est vraiment liee au poste, car cela dependra de ce que l'etape 2 pourra reellement produire plus tard.

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

La logique est :

- niveau atteint ou depasse -> bon score
- legerement en dessous -> score moyen
- plus bas -> score plus faible
- rien detecte -> score faible ou neutre selon le cas

Exemple simple :

- candidat : Licence en informatique -> niveau 3
- poste : Master / Bac+5 -> niveau 4
- comme le candidat est juste un niveau en dessous, on lui donne un score intermediaire, pas un tres mauvais score

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

L'objectif est d'eviter qu'un candidat obtienne artificiellement un score correct juste grace a l'experience ou a la formation alors qu'il manque completement le socle de competences attendu.

---

## 4. Generation des flags pour la suite

Enfin, l'etape 3 genere les flags utiles pour la suite.

L'idee actuelle est simple :

- si le candidat est `RETENU` ou `A_REVOIR`, on peut le transmettre a l'etape suivante
- si besoin, on transmet aussi les competences obligatoires manquantes comme cibles prioritaires

Ca permet a l'etape suivante de savoir quoi faire sans relire toute la logique de scoring.

---

## Comment j'ai teste cette logique

Pour verifier que la logique tenait la route, je l'ai essayee sur plusieurs cas de test simules avec de fausses entrees structurees.

Par exemple :

- un candidat fort avec beaucoup de competences matchees, de l'experience et une bonne formation
- un candidat borderline avec un profil partiellement aligne
- un candidat faible avec peu de competences retrouvees et peu d'experience

L'objectif n'etait pas de prouver scientifiquement que les poids sont parfaits, mais de verifier que :

- le scoring reste coherent
- la decision suit une logique comprehensible
- les cas tres faibles ne passent pas artificiellement
- les cas moyens tombent plutot dans `A_REVOIR`
- les cas forts montent naturellement en `RETENU`

Donc j'ai surtout cherche a voir si le comportement global "a du sens".

---

## Important : cette etape depend forcement des sorties des etapes precedentes

Le point le plus important, c'est que cette etape depend completement de ce que l'etape 1 et surtout l'etape 2 vont reellement fournir.

Donc ce que j'ai fait ici, c'est poser une logique metier claire de l'etape 3.

En gros :

- j'ai essaye de faire une version simple mais coherente de l'etape 3 avec ce qu'on peut deja imaginer comme sortie raisonnable des etapes avant
- si plus tard vous fournissez des signaux plus riches, on pourra raffiner le scoring

Donc pour le moment, je me base sur des elements assez simples :

- les competences obligatoires et appreciees
- ce qui a ete matche ou non
- le nombre de mois d'experience
- les textes de formation

---

## Exemple simple de test

Pour verifier que la logique tenait la route, j'ai aussi essaye un cas simule un peu plus limite, ou le candidat est retenu, mais pas avec une grosse marge.

### Entree simulee

```json
{
  "candidate_id": "C02",
  "candidate_name": "tchehit shawarma wlah",
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
  "candidat_nom": "tchehit shawarma wlah",
  "poste_titre": "Analyste de donnees",
  "score_global": 63.93,
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

Dans ce cas, le candidat est `RETENU`, mais de maniere assez limite :

- il manque encore une competence obligatoire
- son experience est en dessous de ce qui est demande
- sa formation est un peu en dessous du niveau attendu

Donc ce n'est pas un profil "tres fort", mais il passe quand meme le seuil de `RETENU` de justesse.

On peut aussi lire ca sous forme de tableau :

| Partie | Resultat |
|---|---|
| Competences | `63.75` |
| Experience | `62.5` |
| Formation | `68.0` |
| Score global | `63.93` |
| Decision | `RETENU` |

---

## Limites actuelles du scoring

A ce stade, cette logique de scoring reste volontairement simple, donc il y a quelques limites a garder en tete.

- le scoring depend entierement de ce que les etapes 1 et 2 vont reellement fournir  
  donc si leur format final change, la logique de l'etape 3 devra probablement etre adaptee aussi

- la partie experience repose surtout sur le nombre de mois  
  pour l'instant, on regarde surtout si le candidat a moins, autant ou plus d'experience que ce qui est demande, mais on ne mesure pas encore de facon fine si cette experience est vraiment tres liee au poste

- la partie formation repose sur des niveaux detectes a partir de mots-cles  
  ca donne deja une base simple et utile, mais ca reste parfois approximatif selon la maniere dont les diplomes sont formules dans le texte

- le score formation n'est pas encore un score tres fin ou tres progressif  
  on est plutot sur une logique par paliers, donc on n'a pas encore une note tres detaillee en pourcentage sur cette partie

- les poids (`standard`, `junior`, `senior`, `stage`) sont pour l'instant des choix metier simples pour une first prototype
  ils sont coherents pour commencer, mais ils ne viennent pas encore d'un vrai calibrage sur beaucoup de donnees reelles

- certains intitules comme `entry level`, `intermediaire`, `stagiaire`, `internship`, etc.. doivent etre bien normalisés avant d'arriver a cette etape  
  sinon ils risquent de tomber par defaut sur la logique standard

- si les competences obligatoires existent mais que le resultat de matching n'est pas fourni, l'etape retourne `NON_EVALUE`  
  ce choix est volontaire pour eviter de produire un score qui aurait l'air correct alors qu'il manque en realite une partie importante des donnees

Donc pour l'instant, l'objectif n'est pas d'avoir un scoring parfait, mais d'avoir une base coherente, lisible et ajustable quand les sorties reelles des étapes precedentes seront stabilisées.

---

## En resume

De mon cote, l'etape 3 est donc pensée comme :

1. choix des poids selon le poste
2. calcul des scores competences / experience / formation
3. calcul du score global + decision
4. generation des flags pour la suite

La logique est la, mais elle reste adaptable a ce que vous allez réellement sortir cote etapes 1 et 2.

Donc si, de votre cote, vous avez deja une idee plus precise du format final de sortie de l'etape 2, ou si certains champs ne vous semblent pas realistes / utiles, dites-le-moi et je pourrai ajuster le scoring en consequence.
