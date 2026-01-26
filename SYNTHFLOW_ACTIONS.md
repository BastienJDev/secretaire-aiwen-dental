# Configuration des Custom Actions Synthflow - Aiwen Dental Studio

## Informations

- **Cabinet**: Aiwen Dental Studio
- **Praticien**: Dr Lavinia BIRIS
- **ID Praticien**: LB

## URL de base
```
https://votre-app.railway.app
```

---

## 1. Voir les RDV du patient (par telephone)

**Endpoint:** `POST /voir_rdv`

**Description:** Affiche les rendez-vous a venir du patient en utilisant son numero de telephone.

### Configuration Synthflow:

**Name:** `voir_rdv`

**Description:** Affiche les rendez-vous du patient qui appelle

**URL:** `https://votre-app.railway.app/voir_rdv`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "telephone": "{user_phone_number}"
}
```

**Variables utilisees:**
- `{user_phone_number}` - Numero de telephone de l'appelant (automatique)

---

## 2. Annuler un RDV

**Endpoint:** `POST /annuler_rdv`

**Description:** Annule le rendez-vous du patient. Utilise le telephone pour identifier le patient et annule son prochain RDV (ou celui d'une date specifique).

### Configuration Synthflow:

**Name:** `annuler_rdv`

**Description:** Annule le rendez-vous du patient qui appelle

**URL:** `https://votre-app.railway.app/annuler_rdv`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body (version simple - annule le prochain RDV):**
```json
{
  "telephone": "{user_phone_number}"
}
```

**Body (version avec date specifique):**
```json
{
  "telephone": "{user_phone_number}",
  "date_rdv": "{date_rdv}"
}
```

**Variables utilisees:**
- `{user_phone_number}` - Numero de telephone de l'appelant (automatique)
- `{date_rdv}` - Date du RDV a annuler (optionnel, format YYYY-MM-DD ou JJ/MM/AAAA)

---

## 3. Consulter les disponibilites

**Endpoint:** `POST /disponibilites`

**Description:** Retourne les creneaux disponibles pour un type de RDV donne.

### Configuration Synthflow:

**Name:** `disponibilites`

**Description:** Consulte les creneaux disponibles pour prendre rendez-vous

**URL:** `https://votre-app.railway.app/disponibilites`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "type_rdv": "{type_rdv}",
  "date_debut": "{date_debut}",
  "nouveau_patient": true
}
```

**Variables utilisees:**
- `{type_rdv}` - Code du type de RDV (ex: "4" pour controle, "10" pour endo)
- `{date_debut}` - Date de debut de recherche (format YYYY-MM-DD)
- `nouveau_patient` - true/false

---

## 4. Creer un RDV

**Endpoint:** `POST /creer_rdv`

**Description:** Cree un nouveau rendez-vous pour le patient.

### Configuration Synthflow:

**Name:** `creer_rdv`

**Description:** Cree un nouveau rendez-vous

**URL:** `https://votre-app.railway.app/creer_rdv`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
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

**Variables utilisees:**
- `{type_rdv}` - Code du type de RDV
- `{date}` - Date du RDV (format YYYY-MM-DD)
- `{heure}` - Heure du RDV (format HHMM, ex: "0850" pour 8h50)
- `{nom}` - Nom du patient
- `{prenom}` - Prenom du patient
- `{user_phone_number}` - Telephone (automatique)

---

## 5. Rechercher un patient

**Endpoint:** `POST /rechercher_patient`

**Description:** Recherche un patient dans le systeme.

### Configuration Synthflow:

**Name:** `rechercher_patient`

**Description:** Recherche un patient par son telephone

**URL:** `https://votre-app.railway.app/rechercher_patient`

**Method:** `POST`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "telephone": "{user_phone_number}"
}
```

---

## 6. Lister les types de RDV

**Endpoint:** `GET /types_rdv`

**Description:** Liste tous les types de RDV disponibles avec leurs codes.

### Configuration Synthflow:

**Name:** `types_rdv`

**Description:** Liste les types de rendez-vous disponibles

**URL:** `https://votre-app.railway.app/types_rdv`

**Method:** `GET`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

---

## 7. Suggerer un type de RDV

**Endpoint:** `GET /info/suggerer_type_rdv`

**Description:** Suggere le type de RDV adapte au motif du patient.

### Configuration Synthflow:

**Name:** `suggerer_type_rdv`

**Description:** Suggere le type de RDV selon le motif du patient

**URL:** `https://votre-app.railway.app/info/suggerer_type_rdv?motif={motif}`

**Method:** `GET`

**Variables utilisees:**
- `{motif}` - Description du probleme par le patient

---

## Reponses API

Toutes les reponses sont au format JSON avec la structure:

```json
{
  "success": true/false,
  "message": "Message lisible par l'IA",
  ...autres donnees...
}
```

L'IA peut utiliser le champ `message` pour repondre au patient.

---

## Types de RDV courants - Aiwen Dental Studio

| Code | Type | Duree | Restriction horaire |
|------|------|-------|---------------------|
| 4 | Controle | 20 min | Lundi matin, 12h-14h, 16h-17h |
| 6 | Extraction | 20 min | Matin uniquement |
| 7 | Empreinte | 50 min | Matin uniquement |
| 10 | Endo | 60 min | Matin uniquement |
| 13 | Pose | 20 min | Lundi matin, 12h-14h |
| 34 | Bilan | 30 min | Lundi matin, 12h-14h, 16h-17h |
| 35 | Detartrage | 20 min | Lundi matin, 12h-14h, 16h-17h |
| 36-38 | Urgences | 20 min | Toute la journee |
| 75 | Douleur | 20 min | Toute la journee |
| 84 | Nouveau patient | 30 min | Jeudi (surtout apres-midi) |
| 102 | MEOPA | 60 min | Matin uniquement |

---

## Notes importantes

1. **Telephone automatique**: Utilisez `{user_phone_number}` pour recuperer automatiquement le numero de l'appelant.

2. **Formats de date acceptes**:
   - ISO: `2026-01-23`
   - Francais: `23/01/2026`

3. **Format d'heure**: Toujours en HHMM (ex: `0850` pour 8h50, `1400` pour 14h00)

4. **Praticien**: Le praticien par defaut est "LB" (Dr Lavinia BIRIS).

5. **Horaires**: Lundi-Jeudi 08h50-17h45. Ferme Vendredi-Dimanche.

6. **Regles de planification**:
   - Nouveaux patients: Jeudi de preference (surtout apres-midi)
   - Gros RDV (Endo, Empreinte, MEOPA): Matin uniquement
   - Extractions: Matin uniquement
   - Controles/Poses: Lundi matin ou 12h-14h
