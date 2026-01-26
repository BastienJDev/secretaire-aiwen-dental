# Configuration Synthflow/Fine-tuner - Aiwen Dental Studio

## Informations du Cabinet

- **Nom du cabinet**: Aiwen Dental Studio
- **Praticien**: Dr Lavinia BIRIS
- **ID Praticien**: LB

---

## Etape 1 : Deployer sur Railway

1. Creer un compte sur [Railway](https://railway.app)
2. Connecter votre GitHub
3. Creer un nouveau projet depuis ce repo
4. **Ajouter les variables d'environnement** (onglet Variables) :
   - `RDVDENTISTE_API_KEY` : `DYND-457AD3+21ZDZX-sdm3ISX`
   - `RDVDENTISTE_OFFICE_CODE` : `100604704JWYKTPKJOOI`
5. Railway deploiera automatiquement
6. Recuperer l'URL (ex: `https://votre-app.up.railway.app`)

---

## Etape 2 : Configurer les Custom Actions dans Synthflow

Dans votre dashboard Synthflow/Fine-tuner, creez les actions suivantes.

### Variables Synthflow

| Variable | Description | Auto |
|----------|-------------|------|
| `{user_phone_number}` | Numero de l'appelant | OUI (automatique) |
| `{type_rdv}` | Code numerique du RDV (ex: "4", "10") | NON |
| `{date_debut}` | Date debut recherche (YYYY-MM-DD) | NON |
| `{date}` | Date du RDV (YYYY-MM-DD) | NON |
| `{heure}` | Heure format HHMM (ex: "0850") | NON |
| `{nom}` | Nom du patient | NON |
| `{prenom}` | Prenom du patient | NON |
| `{date_rdv}` | Date RDV a annuler (optionnel) | NON |
| `{motif}` | Description du probleme | NON |

---

## Actions principales (gestion RDV)

### Action 1 : Rechercher un patient

**Nom de l'action:** `rechercher_patient`

**Description pour l'IA:**
> Utilise cette action pour rechercher un patient existant dans le systeme par son numero de telephone.

**Configuration API:**
- **Methode:** POST
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/rechercher_patient`
- **Headers:**
  - `Content-Type: application/json`

**Body (JSON):**
```json
{
  "telephone": "{user_phone_number}"
}
```

**Variables:** Aucune a creer (telephone automatique)

---

### Action 2 : Consulter les disponibilites

**Nom de l'action:** `consulter_disponibilites`

**Description pour l'IA:**
> Utilise cette action pour voir les creneaux disponibles. Demande d'abord au patient quel type de rendez-vous il souhaite et a partir de quelle date. Utilise les codes numeriques pour le type de RDV.

**Configuration API:**
- **Methode:** POST
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/consulter_disponibilites`
- **Headers:**
  - `Content-Type: application/json`

**Body (JSON):**
```json
{
  "type_rdv": "{type_rdv}",
  "date_debut": "{date_debut}",
  "nouveau_patient": true
}
```

**Variables a creer:**
| Variable | Description | Exemple |
|----------|-------------|---------|
| type_rdv | Code numerique du type de RDV | "4" |
| date_debut | Date de debut de recherche | "2026-01-27" |

---

### Action 3 : Creer un rendez-vous

**Nom de l'action:** `creer_rdv`

**Description pour l'IA:**
> Utilise cette action pour reserver un creneau une fois que le patient a choisi une date et une heure. Tu dois avoir le nom et prenom du patient.

**Configuration API:**
- **Methode:** POST
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/creer_rdv`
- **Headers:**
  - `Content-Type: application/json`

**Body (JSON):**
```json
{
  "type_rdv": "{type_rdv}",
  "date": "{date}",
  "heure": "{heure}",
  "nom": "{nom}",
  "prenom": "{prenom}",
  "telephone": "{user_phone_number}",
  "nouveau_patient": true
}
```

**Variables a creer:**
| Variable | Description | Exemple |
|----------|-------------|---------|
| type_rdv | Code numerique du type de RDV | "4" |
| date | Date du RDV | "2026-01-28" |
| heure | Heure format HHMM | "0850" |
| nom | Nom du patient | "DUPONT" |
| prenom | Prenom du patient | "Marie" |

---

### Action 4 : Voir les RDV d'un patient

**Nom de l'action:** `voir_rdv`

**Description pour l'IA:**
> Utilise cette action pour afficher tous les rendez-vous d'un patient. Le telephone est recupere automatiquement.

**Configuration API:**
- **Methode:** POST
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/voir_rdv`
- **Headers:**
  - `Content-Type: application/json`

**Body (JSON):**
```json
{
  "telephone": "{user_phone_number}"
}
```

**Variables:** Aucune a creer (telephone automatique)

---

### Action 5 : Annuler un RDV

**Nom de l'action:** `annuler_rdv`

**Description pour l'IA:**
> Utilise cette action pour annuler un rendez-vous existant. Le telephone est recupere automatiquement. Si le patient a plusieurs RDV, demande la date du RDV a annuler.

**Configuration API:**
- **Methode:** POST
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/annuler_rdv`
- **Headers:**
  - `Content-Type: application/json`

**Body (JSON):**
```json
{
  "telephone": "{user_phone_number}",
  "date_rdv": "{date_rdv}"
}
```

**Variables a creer:**
| Variable | Description | Exemple |
|----------|-------------|---------|
| date_rdv | Date du RDV a annuler (optionnel) | "2026-01-28" |

---

### Action 6 : Suggerer un type de RDV

**Nom de l'action:** `suggerer_type_rdv`

**Description pour l'IA:**
> Utilise cette action quand le patient decrit son probleme mais ne sait pas quel type de RDV prendre.

**Configuration API:**
- **Methode:** GET
- **URL:** `https://VOTRE-URL-RAILWAY.up.railway.app/info/suggerer_type_rdv?motif={motif}`

**Variables a creer:**
| Variable | Description | Exemple |
|----------|-------------|---------|
| motif | Description du probleme | "j'ai mal a une dent" |

---

## Etape 3 : Configurer le prompt systeme de l'agent

Voici le prompt systeme pour la secretaire IA d'Aiwen Dental Studio :

```
Tu es la secretaire virtuelle du cabinet Aiwen Dental Studio du Dr Lavinia BIRIS.

Ton role :
- Accueillir chaleureusement les patients
- Les aider a prendre, modifier ou annuler des rendez-vous
- Repondre aux questions sur les horaires et types de consultations

Comportement :
- Sois professionnelle mais chaleureuse
- Pose les questions une par une, ne submerge pas le patient
- Confirme toujours les informations avant de creer un RDV
- Si tu ne peux pas aider, propose de laisser un message pour le cabinet

Flux typique pour un nouveau RDV :
1. Demande si le patient est deja venu au cabinet
2. Si oui, recherche-le avec nom + prenom + telephone
3. Demande le motif de consultation (utilise suggerer_type_rdv si besoin)
4. Propose les creneaux disponibles
5. Confirme les informations et cree le RDV
6. Rappelle au patient qu'il recevra une confirmation

Horaires du cabinet :
- Lundi : 08h50-17h45
- Mardi : 08h50-17h45
- Mercredi : 08h50-17h45
- Jeudi : 08h50-17h45
- Vendredi : FERME
- Samedi : FERME
- Dimanche : FERME

Note: Le premier RDV est a 08h50 (09h00 sur le planning), le dernier RDV a 17h00 (17h10 sur le planning).

Regles de planification importantes :
- Nouveaux patients : Preferer le JEUDI, surtout l'apres-midi
- Gros RDV (Empreinte, Endo, MEOPA) : Matin uniquement, Mardi-Jeudi de preference
- Extractions/Chirurgie : TOUJOURS le matin
- Controles et Poses : Lundi matin ou entre 12h-14h tous les jours
- Controles/Bilans : Aussi possibles en fin de journee (16h-17h)

Types de RDV disponibles (avec codes numeriques) :

SOINS COURANTS :
- 4 : Controle (20 min)
- 34 : Bilan (30 min)
- 35 : Detartrage (20 min)
- 8 : Radio (20 min)
- 12 : Reparation (20 min)
- 15 : Sealent (20 min)

URGENCES :
- 36 : Urgence patient en cours (20 min)
- 37 : Urgence patient du cabinet (20 min)
- 38 : Urgence externe (20 min)
- 75 : Douleur (20 min)
- 82 : Dent cassee (20 min)
- 83 : Couronne a resceller (20 min)

SOINS LONGS (matin uniquement) :
- 7 : Empreinte (50 min)
- 10 : Endo (60 min)
- 11 : Reendo (60 min)
- 14 : Soins mylolyse (50 min)
- 102 : MEOPA (60 min)

EXTRACTIONS (matin uniquement) :
- 6 : Extraction (20 min)
- 47 : Extraction dent lacteale (20 min)
- 48 : Extraction dent definitive (30 min)

POSES (lundi matin ou 12h-14h) :
- 13 : Pose (20 min)
- 43 : Pose appareil amovible (10 min)
- 73 : Pose reparation (10 min)

NOUVEAUX PATIENTS (jeudi de preference) :
- 84 : Nouveau patient autre (30 min)
- 70 : Nouveau patient recommande (30 min)

AUTRES :
- 9 : Rebasage (20 min)
- 17 : Empreinte gouttiere bruxisme (10 min)
- 40 : Empreinte gouttiere blanchiment (20 min)
- 55 : Motivation au brossage (10 min)
- 57 : Obturation de chambre (20 min)
- 65 : Presentation plan de traitement (20 min)
- 67 : Surfacage (30 min)
- 69 : Essayage (10 min)
- 71 : Empreinte II + Occlusion (20 min)
- 77 : Probleme DDS (20 min)
- 93 : Scanner (20 min)
- 94 : Fils de suture (10 min)

Format heure : HHMM (ex: "0850" pour 8h50, "1400" pour 14h00)
```

---

## Referentiel des types de RDV (Codes API)

**IMPORTANT : Utiliser les codes numeriques pour les appels API**

| Code | Nom | Duree | Plage horaire |
|------|-----|-------|---------------|
| 4 | CONTROLE | 20 min | Lundi matin, 12h-14h, fin de journee |
| 6 | EXTRACTION | 20 min | Matin uniquement |
| 7 | EMPREINTE | 50 min | Matin uniquement |
| 8 | Radio | 20 min | Toute la journee |
| 9 | REBASAGE | 20 min | Toute la journee |
| 10 | ENDO | 60 min | Matin uniquement |
| 11 | REENDO | 60 min | Matin uniquement |
| 12 | Reparation | 20 min | Toute la journee |
| 13 | POSE | 20 min | Lundi matin, 12h-14h |
| 14 | SOINS | 50 min | Matin uniquement |
| 15 | SEALENT | 20 min | Toute la journee |
| 17 | EMP GOUTIERE BRUXISME | 10 min | Toute la journee |
| 34 | BILAN | 30 min | Lundi matin, 12h-14h, fin de journee |
| 35 | DET | 20 min | Lundi matin, 12h-14h, fin de journee |
| 36 | URGENCE PATIENT EN COURS | 20 min | Toute la journee |
| 37 | URGENCE PATIENT DU CABINET | 20 min | Toute la journee |
| 38 | URGENCE EXTERNE | 20 min | Toute la journee |
| 40 | EMP GOUT BLANCHIMENT | 20 min | Toute la journee |
| 43 | POSE APPAREIL AMOVIBLE | 10 min | Lundi matin, 12h-14h |
| 47 | EXTRACTION DENT LACTEALE | 20 min | Matin uniquement |
| 48 | EXTRACTION DENT DEFINITIVE | 30 min | Matin uniquement |
| 55 | MOTIVATION AU BROSSAGE | 10 min | Toute la journee |
| 57 | OBTURATION DE CHAMBRE | 20 min | Toute la journee |
| 65 | PRESENTATION PLAN TRAITEMENT | 20 min | Toute la journee |
| 67 | SURFACAGE | 30 min | Toute la journee |
| 69 | ESSAYAGE | 10 min | Toute la journee |
| 70 | NOUVEAU PATIENT RECOMMANDE | 30 min | Jeudi (surtout apres-midi) |
| 71 | EMP II + OCCLUSION | 20 min | Toute la journee |
| 73 | POSE REPARATION | 10 min | Lundi matin, 12h-14h |
| 75 | DOULEUR | 20 min | Toute la journee |
| 77 | PROBLEME DDS | 20 min | Toute la journee |
| 82 | DENT CASSEE | 20 min | Toute la journee |
| 83 | COURONNE A RESCELLER | 20 min | Toute la journee |
| 84 | NOUVEAU PATIENT AUTRE | 30 min | Jeudi (surtout apres-midi) |
| 93 | SCANNER | 20 min | Toute la journee |
| 94 | FILS DE SUTURE | 10 min | Toute la journee |
| 102 | MEOPA | 60 min | Matin uniquement |

---

## Regles de planification

| Categorie | Jours | Horaires |
|-----------|-------|----------|
| Gros RDV (>30min) | Lundi-Jeudi | 08h50-12h00 (matin) |
| Extraction/Chirurgie | Lundi-Jeudi | 08h50-12h00 (matin) |
| Controles/Bilans | Lundi-Jeudi | Lundi matin, 12h-14h, 16h-17h |
| Poses | Lundi-Jeudi | Lundi matin, 12h-14h |
| Nouveaux patients | Jeudi | 12h00-17h00 (surtout apres-midi) |
| Urgences | Lundi-Jeudi | 08h50-17h00 |
| Standard | Lundi-Jeudi | 08h50-17h00 |

---

## Notes importantes

- **Office Code** : `100604704JWYKTPKJOOI`
- **API Key** : `DYND-457AD3+21ZDZX-sdm3ISX`
- **Praticien ID** : `LB` (Dr Lavinia BIRIS)
- **Dates** : L'API accepte les formats YYYY-MM-DD et JJ/MM/AAAA (conversion automatique)
- **Format heure** : HHMM (ex: "0850" pour 8h50, "1400" pour 14h00)
- **Cabinet ferme** : Vendredi, Samedi, Dimanche
- **Premier RDV** : 08h50 (09h00 sur le planning)
- **Dernier RDV** : 17h00 (17h10 sur le planning)
