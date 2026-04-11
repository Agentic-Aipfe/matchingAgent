# Étape 3 — Scoring & Décision

HOLA AMIGOS

welll de  mon côté, j’ai travaillé sur l’étape 3 de l’Agent 2, c’est à dire la partie **scoring et prise de décision** après le matching CV ↔ offre.

L’idée ici est de poser une logique simple  pour transformer les résultats du matching en :

- un score global
- une décision
- des détails par critère
- des flags pour la suite du pipeline

Je suis parti de ce qu’une étape “Scoring & Decision” doit naturellement faire, de la slide de l’étape 3, et aussi de l’exemple JSON qu’on avait déjà dans l’étape 4 du rapport final.

Donc j’ai structuré l’étape 3 autour de 4 tâches.

---

## 1. Attribution des poids selon le poste

La première chose que fait l’étape 3, c’est choisir un profil de pondération selon le type ou le niveau du poste.

J’ai gardé 4 profils simples :

- `standard`
- `junior`
- `senior`
- `stage`

L’idée derrière ça est assez naturelle :

- pour un poste standard, les compétences restent le critère principal  (ca couvre aussi les postes Intermediaires)
- pour un junior, la formation compte un peu plus
- pour un senior, l’expérience compte plus
- pour un stage, la formation et le potentiel comptent davantage

Donc avant même de calculer le score, on décide avec quels poids on va lire le profil du candidat.

---

## 2. Calcul des scores par dimension

J’ai séparé le scoring en 3 dimensions :

- compétences
- expérience
- formation

### Compétences

Le score compétences repose surtout sur :

- les compétences obligatoires retrouvées
- les compétences appréciées retrouvées
- les compétences obligatoires manquantes

Dans la logique actuelle :

- les compétences obligatoires pèsent le plus
- les compétences appréciées donnent un bonus
- mais ce bonus ne doit pas compenser totalement une absence sur les obligatoires

 Exemple simple :

- l’offre demande comme compétences obligatoires : Python, SQL, Docker
- le candidat a : Python et SQL
- il lui manque : Docker

Donc les compétences obligatoires retrouvées sont 2 sur 3, et la base du score compétences part de là.

Si le candidat a aussi une compétence appréciée retrouvée, elle peut ajouter un petit bonus, mais elle ne remplace pas une compétence obligatoire manquante.


Donc si un candidat n’a rien sur les obligatoires, il ne peut pas être sauvé uniquement par des compétences “bonus”.

### Expérience

Pour l’instant, dans cette vesion at leaast, l’expérience est notée de manière simple à partir des mois :

- expérience totale du candidat(on doit calculer exp_month_total du candidat, on l'a pas encore fait imken)
- expérience demandée par le poste

Si le poste précise une durée attendue, on compare les mois du candidat à cette durée.
Si aucune durée n’est précisée, on utilise une règle simple basée sur le total de mois.

Je n’ai pas ajouté ici une logique plus avancée pour savoir si l’expérience est vraiment liée au poste, car cela dépendra de ce que l’étape 2 pourra réellement produire plus tard.


### Formation

Pour la formation, j’ai utilisé une logique simple de détection du niveau à partir du texte :

- doctorat
- bac+5 / master / ingénieur / msc / mba
- bac+3 / licence / bachelor
- bac+2 / dut / bts
- bac

Ensuite on compare :

- le niveau détecté côté candidat
- le niveau détecté côté poste

La logique est :

- niveau atteint ou dépassé -> bon score
- légèrement en dessous -> score moyen
- plus bas -> score plus faible
- rien détecté -> score faible ou neutre selon le cas

 Exemple simple :

- candidat : Licence en informatique -> niveau 3
- poste : Master / Bac+5 -> niveau 4
- comme le candidat est juste un niveau en dessous, on lui donne un score intermédiaire, pas un très mauvais score


Donc ici on est sur une logique de niveau, pas encore sur une logique fine de spécialisation.

---

## 3. Calcul du score global et décision

Une fois les 3 sous-scores calculés, on applique les poids du poste pour produire un score global.

Ensuite ce score global est transformé en décision selon des seuils simples :

- `RETENU`
- `A_REVOIR`
- `REJETE`

J’ai aussi ajouté un garde-fou :

si le poste a des compétences obligatoires mais qu’aucune n’a été retrouvée, alors le score global est plafonné.
L’objectif est d’éviter qu’un candidat obtienne artificiellement un score correct juste grâce à l’expérience ou à la formation alors qu’il manque complètement le socle de compétences attendu.

---

## 4. Génération des flags pour la suite

Enfin, l’étape 3 génère les flags utiles pour la suite du pipeline.

L’idée actuelle est simple :

- si le candidat est `RETENU` ou `A_REVOIR`, on peut le transmettre à l’étape suivante
- si besoin, on transmet aussi les compétences obligatoires manquantes comme cibles prioritaires

Ça permet à l’étape suivante de savoir quoi faire sans relire toute la logique de scoring.

---

## Comment j’ai testé cette logique

Pour vérifier que la logique tenait la route, je l’ai essayée sur plusieurs cas de test simulés avec de fausses entrées structurées.

Par exemple :

- un candidat fort avec beaucoup de compétences matchées, de l’expérience et une bonne formation
- un candidat borderline avec un profil partiellement aligné
- un candidat faible avec peu de compétences retrouvées et peu d’expérience

L’objectif n’était pas de prouver scientifiquement que les poids sont parfaits, mais de vérifier que :

- le scoring reste cohérent
- la décision suit une logique compréhensible
- les cas très faibles ne passent pas artificiellement
- les cas moyens tombent plutôt dans `A_REVOIR`
- les cas forts montent naturellement en `RETENU`

Donc j’ai surtout cherché à voir si le comportement global “a du sens”.

---

## Important : cette étape dépend forcément des sorties des étapes précédentes

Le point le plus important, c’est que cette étape dépend complètement de ce que l’étape 1 et surtout l’étape 2 vont réellement fournir.

Donc ce que j’ai fait ici, c’est poser une logique métier claire de l'étape 3.

En gros :

-j’ai essayé de faire une version simple mais cohérente de l’étape 3 avec ce qu’on peut déjà imaginer comme sortie raisonnable des étapes avant.
- si plus tard vous fournissez des signaux plus riches, on pourra raffiner le scoring.

Donc pour le moment, je me base sur des éléments assez simples :

- les compétences obligatoires et appréciées
- ce qui a été matché ou non
- le nombre de mois d’expérience
- les textes de formation


---

## En résumé

De mon côté, l’étape 3 est donc pensée comme :

1. choix des poids selon le poste
2. calcul des scores compétences / expérience / formation
3. calcul du score global + décision
4. génération des flags pour la suite

La logique est là, mais elle reste adaptable à ce que vous allez réellement sortir côté étapes 1 et 2.

Donc si, de votre côté, vous avez déjà une idée plus précise du format final de sortie de l’étape 2, ou si certains champs ne vous semblent pas réalistes / utiles, dites-le-moi et je pourrai ajuster le scoring en conséquence.
