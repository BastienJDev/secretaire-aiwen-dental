"""
Secrétaire IA - Middleware pour rdvdentiste.net / Logosw
Backend FastAPI pour Synthflow Custom Actions

Version: 2.0.0
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
from datetime import datetime, timedelta
import re
import os

# ============== CONFIGURATION ==============

app = FastAPI(
    title="Secrétaire IA Dentiste",
    description="Middleware pour connecter Synthflow à l'API rdvdentiste.net",
    version="2.0.0"
)

RDVDENTISTE_BASE_URL = "https://www.rdvdentiste.net/api"
DEFAULT_OFFICE_CODE = os.getenv("RDVDENTISTE_OFFICE_CODE", "0501463005IMZDB742BK")
DEFAULT_API_KEY = os.getenv("RDVDENTISTE_API_KEY")
DEFAULT_PRATICIEN_ID = "MC"


# ============== FONCTIONS UTILITAIRES ==============

def normaliser_telephone(telephone: str) -> str:
    """
    Normalise un numéro de téléphone français.
    Accepte: "+33683791443", "06 83 79 14 43", "0033683791443", "0683791443"
    Retourne: "0683791443"
    """
    if not telephone:
        return telephone

    # Supprimer espaces, tirets, points, parenthèses
    tel = re.sub(r'[\s\-\.\(\)]', '', telephone)

    # Gérer les différents formats
    if tel.startswith('+33'):
        tel = '0' + tel[3:]
    elif tel.startswith('0033'):
        tel = '0' + tel[4:]
    elif tel.startswith('33') and len(tel) > 10:
        tel = '0' + tel[2:]

    return tel


def convertir_date(date_str: str) -> str:
    """
    Convertit une date vers le format ISO (YYYY-MM-DD).
    Accepte: "JJ/MM/AAAA", "JJ-MM-AAAA", "YYYY-MM-DD"
    """
    if not date_str:
        return date_str

    # Déjà au format ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Format JJ/MM/AAAA
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        jour, mois, annee = date_str.split('/')
        return f"{annee}-{mois}-{jour}"

    # Format JJ-MM-AAAA
    if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        jour, mois, annee = date_str.split('-')
        return f"{annee}-{mois}-{jour}"

    return date_str


def formater_heure(heure: str) -> str:
    """Formate une heure HHMM en HHhMM"""
    if len(heure) == 4:
        return f"{heure[:2]}h{heure[2:]}"
    return heure


# ============== CLIENT API RDVDENTISTE ==============

async def call_rdvdentiste(
    method: str,
    endpoint: str,
    office_code: str,
    api_key: Optional[str] = None,
    params: dict = None,
    json_data: dict = None,
    allow_404: bool = False
) -> dict:
    """Appel générique à l'API rdvdentiste"""
    effective_api_key = api_key or DEFAULT_API_KEY

    headers = {
        "OfficeCode": office_code,
        "Content-Type": "application/json"
    }
    if effective_api_key:
        headers["ApiKey"] = effective_api_key

    url = f"{RDVDENTISTE_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "PUT":
                response = await client.put(url, headers=headers, params=params, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                response = await client.post(url, headers=headers, params=params, json=json_data)

            # Gérer les cas spéciaux
            if allow_404 and response.status_code == 404:
                try:
                    return response.json()
                except:
                    return {"Error": {"code": "notFound", "text": "Not found"}}

            if response.status_code == 400:
                try:
                    return response.json()
                except:
                    pass

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout lors de l'appel à l'API")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


async def trouver_patients_par_telephone(telephone: str, office_code: str, api_key: Optional[str]) -> List[dict]:
    """Recherche tous les patients avec un numéro de téléphone donné"""
    tel_normalise = normaliser_telephone(telephone)
    search_result = await call_rdvdentiste(
        "GET", "/patients/find", office_code, api_key,
        {"mobile": tel_normalise}, allow_404=True
    )

    patients = []
    if isinstance(search_result, dict) and "Patients" in search_result:
        for patient in search_result.get("Patients", []):
            patient_id = patient.get("identifier") or patient.get("id")
            if patient_id:
                patients.append({
                    "id": patient_id,
                    "nom": patient.get("lastName") or patient.get("family"),
                    "prenom": patient.get("firstName") or patient.get("given"),
                    "data": patient
                })

    return patients


async def trouver_rdvs_patient(patient_id: str, office_code: str, api_key: Optional[str]) -> List[dict]:
    """Récupère tous les RDV d'un patient"""
    result = await call_rdvdentiste("GET", f"/patients/{patient_id}/appointments", office_code, api_key)

    print(f"[TROUVER_RDVS] Patient {patient_id} - Réponse brute API: {result}")

    rdvs = []
    if isinstance(result, list):
        for rdv in result:
            service_type = rdv.get("service_type", {})
            rdv_id = rdv.get("rdvId") or rdv.get("id")
            rdv_status = rdv.get("status", "Confirmé")
            print(f"[TROUVER_RDVS] RDV trouvé: id={rdv_id}, status={rdv_status}, raw={rdv}")
            rdvs.append({
                "id": rdv_id,
                "patient_id": patient_id,
                "date": rdv.get("date"),
                "heure": rdv.get("start") or rdv.get("hour"),
                "type": service_type.get("display") if isinstance(service_type, dict) else rdv.get("type"),
                "duree_minutes": rdv.get("duration"),
                "statut": rdv_status
            })

    return rdvs


# ============== MODÈLES PYDANTIC ==============

# --- Recherche Patient ---
class RechercherPatientRequest(BaseModel):
    telephone: Optional[str] = Field(None, description="Numéro de téléphone du patient")
    nom: Optional[str] = Field(None, description="Nom de famille")
    prenom: Optional[str] = Field(None, description="Prénom")
    date_naissance: Optional[str] = Field(None, description="Date de naissance (YYYY-MM-DD ou JJ/MM/AAAA)")


# --- Voir RDV ---
class VoirRdvRequest(BaseModel):
    telephone: str = Field(..., description="Téléphone du patient (utiliser {user_phone_number} dans Synthflow)")


# --- Annuler RDV ---
class AnnulerRdvRequest(BaseModel):
    telephone: str = Field(..., description="Téléphone du patient (utiliser {user_phone_number} dans Synthflow)")
    date_rdv: Optional[str] = Field(None, description="Date du RDV à annuler (optionnel, format YYYY-MM-DD ou JJ/MM/AAAA)")


# --- Consulter Disponibilités ---
class DisponibilitesRequest(BaseModel):
    type_rdv: str = Field(..., description="Code du type de RDV (ex: 84, 27)")
    date_debut: str = Field(..., description="Date de début (YYYY-MM-DD ou JJ/MM/AAAA)")
    date_fin: Optional[str] = Field(None, description="Date de fin (par défaut +7 jours)")
    nouveau_patient: Optional[bool] = Field(False, description="Est-ce un nouveau patient ?")


# --- Créer RDV ---
class CreerRdvRequest(BaseModel):
    type_rdv: str = Field(..., description="Code du type de RDV")
    date: str = Field(..., description="Date du RDV (YYYY-MM-DD ou JJ/MM/AAAA)")
    heure: str = Field(..., description="Heure du RDV (format HHMM, ex: 0930 pour 9h30)")
    nom: str = Field(..., description="Nom du patient")
    prenom: str = Field(..., description="Prénom du patient")
    telephone: str = Field(..., description="Téléphone du patient")
    email: Optional[str] = Field(None, description="Email du patient")
    date_naissance: Optional[str] = Field(None, description="Date de naissance")
    nouveau_patient: Optional[bool] = Field(True, description="Est-ce un nouveau patient ?")
    message: Optional[str] = Field(None, description="Message pour le praticien")


# ============== ENDPOINTS PRINCIPAUX ==============

@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "Secrétaire IA Dentiste", "version": "2.0.0"}


# ----- 1. VOIR LES RDV D'UN PATIENT (par téléphone) -----

@app.post("/voir_rdv")
async def voir_rdv(
    request: VoirRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    📅 VOIR LES RDV D'UN PATIENT

    Utilise le numéro de téléphone pour retrouver le patient et ses RDV.
    Dans Synthflow, utiliser {user_phone_number} pour le téléphone.

    Recherche automatiquement tous les patients avec ce numéro.
    """
    telephone = normaliser_telephone(request.telephone)

    # Trouver tous les patients avec ce numéro
    patients = await trouver_patients_par_telephone(telephone, office_code, api_key)

    if not patients:
        return {
            "success": False,
            "message": "Je n'ai trouvé aucun patient avec ce numéro de téléphone dans notre système."
        }

    # Collecter les RDV de tous les patients
    tous_rdvs = []
    for patient in patients:
        rdvs = await trouver_rdvs_patient(patient["id"], office_code, api_key)
        tous_rdvs.extend(rdvs)

    # Filtrer uniquement les RDV actifs/futurs
    rdvs_actifs = [r for r in tous_rdvs if r.get("statut") == "active"]

    if not rdvs_actifs:
        return {
            "success": True,
            "telephone": telephone,
            "rdvs": [],
            "nombre_rdvs": 0,
            "message": "Vous n'avez pas de rendez-vous à venir."
        }

    # Formater pour une réponse claire
    rdvs_formates = []
    for rdv in rdvs_actifs:
        rdvs_formates.append({
            "id": rdv["id"],
            "date": rdv["date"],
            "heure": rdv["heure"],
            "type": rdv["type"]
        })

    return {
        "success": True,
        "telephone": telephone,
        "rdvs": rdvs_formates,
        "nombre_rdvs": len(rdvs_formates),
        "message": f"Vous avez {len(rdvs_formates)} rendez-vous à venir."
    }


# ----- 2. ANNULER UN RDV (par téléphone) -----

@app.post("/annuler_rdv")
async def annuler_rdv(
    request: AnnulerRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    ❌ ANNULER UN RDV

    Utilise le numéro de téléphone pour retrouver le patient et annuler son RDV.
    Si date_rdv est fourni, annule le RDV de cette date spécifique.
    Sinon, annule le prochain RDV.

    Dans Synthflow, utiliser {user_phone_number} pour le téléphone.
    """
    telephone = normaliser_telephone(request.telephone)

    # Ignorer date_rdv si c'est une variable non remplacée ou vide
    date_rdv_raw = request.date_rdv
    if date_rdv_raw and (date_rdv_raw.startswith("<") or date_rdv_raw.startswith("{") or date_rdv_raw == ""):
        date_rdv_raw = None
    date_cible = convertir_date(date_rdv_raw) if date_rdv_raw else None

    # Trouver tous les patients avec ce numéro
    patients = await trouver_patients_par_telephone(telephone, office_code, api_key)

    if not patients:
        return {
            "success": False,
            "message": "Je n'ai trouvé aucun patient avec ce numéro de téléphone."
        }

    # Chercher tous les RDV actifs
    tous_rdvs_actifs = []
    for patient in patients:
        rdvs = await trouver_rdvs_patient(patient["id"], office_code, api_key)
        for rdv in rdvs:
            if rdv.get("statut") == "active":
                tous_rdvs_actifs.append(rdv)

    print(f"[ANNULER_RDV] Tous les RDV actifs trouvés: {tous_rdvs_actifs}")

    # Trier par date (plus proche en premier)
    today = datetime.now().strftime("%Y-%m-%d")
    tous_rdvs_actifs_futurs = [r for r in tous_rdvs_actifs if r.get("date", "") >= today]
    tous_rdvs_actifs_futurs.sort(key=lambda r: r.get("date", "9999-99-99"))

    print(f"[ANNULER_RDV] RDV futurs triés: {tous_rdvs_actifs_futurs}")

    # Sélectionner le RDV à annuler
    rdv_a_annuler = None
    if date_cible:
        # Chercher un RDV à la date spécifiée
        for rdv in tous_rdvs_actifs_futurs:
            if rdv.get("date") == date_cible:
                rdv_a_annuler = rdv
                break
    else:
        # Prendre le prochain RDV (le plus proche dans le futur)
        if tous_rdvs_actifs_futurs:
            rdv_a_annuler = tous_rdvs_actifs_futurs[0]

    if not rdv_a_annuler:
        msg = "Aucun rendez-vous actif trouvé"
        if date_cible:
            msg += f" pour le {date_cible}"
        return {"success": False, "message": msg}

    rdv_id = rdv_a_annuler["id"]
    rdv_statut_original = rdv_a_annuler.get("statut")

    # Log pour debug
    print(f"[ANNULER_RDV] RDV trouvé: id={rdv_id}, statut={rdv_statut_original}, date={rdv_a_annuler.get('date')}")

    # Déterminer le bon endpoint (appointment vs appointment-request)
    if rdv_id.upper().startswith("D"):
        endpoint = f"/schedules/{DEFAULT_PRATICIEN_ID}/appointments/{rdv_id}/"
    else:
        endpoint = f"/schedules/{DEFAULT_PRATICIEN_ID}/appointment-requests/{rdv_id}/"

    print(f"[ANNULER_RDV] Endpoint utilisé: DELETE {endpoint}")

    # Appeler l'API pour annuler
    result = await call_rdvdentiste("DELETE", endpoint, office_code, api_key)

    print(f"[ANNULER_RDV] Réponse API: {result}")

    # Vérifier le résultat
    error_msg = None
    if isinstance(result, dict):
        error_msg = result.get("error") or result.get("Error")
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("text") or error_msg.get("message") or str(error_msg)

    if error_msg:
        if "already cancelled" in str(error_msg).lower() or "déjà annulé" in str(error_msg).lower():
            return {
                "success": True,
                "message": f"Ce rendez-vous du {rdv_a_annuler['date']} était déjà annulé."
            }
        return {
            "success": False,
            "message": f"Erreur lors de l'annulation: {error_msg}"
        }

    return {
        "success": True,
        "rdv_id": rdv_id,
        "date": rdv_a_annuler["date"],
        "heure": rdv_a_annuler["heure"],
        "message": f"Votre rendez-vous du {rdv_a_annuler['date']} à {rdv_a_annuler['heure']} a bien été annulé."
    }


# ----- 3. CONSULTER LES DISPONIBILITÉS -----

@app.post("/disponibilites")
async def consulter_disponibilites(
    request: DisponibilitesRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    🗓️ CONSULTER LES DISPONIBILITÉS

    Retourne les créneaux disponibles pour un type de RDV donné.
    """
    date_debut = convertir_date(request.date_debut)

    # Date de fin par défaut: +7 jours
    if request.date_fin:
        date_fin = convertir_date(request.date_fin)
    else:
        date_debut_obj = datetime.strptime(date_debut, "%Y-%m-%d")
        date_fin = (date_debut_obj + timedelta(days=7)).strftime("%Y-%m-%d")

    params = {
        "start": date_debut,
        "end": date_fin,
        "newPatient": "1" if request.nouveau_patient else "0"
    }

    endpoint = f"/schedules/{DEFAULT_PRATICIEN_ID}/slots/{request.type_rdv}/"
    result = await call_rdvdentiste("GET", endpoint, office_code, api_key, params)

    # Parser les créneaux
    creneaux = []
    slots = result.get("AvailableSlots", []) if isinstance(result, dict) else result

    for slot in slots:
        start_time = slot.get("start", "")
        if start_time:
            date_part = start_time.split("T")[0]
            time_part = start_time.split("T")[1][:5]
            heure_code = time_part.replace(":", "")
            creneaux.append({
                "date": date_part,
                "heure": heure_code,
                "heure_affichage": time_part.replace(":", "h")
            })

    return {
        "success": True,
        "type_rdv": request.type_rdv,
        "periode": f"Du {date_debut} au {date_fin}",
        "creneaux": creneaux,
        "nombre_creneaux": len(creneaux),
        "message": f"{len(creneaux)} créneaux disponibles." if creneaux else "Aucun créneau disponible sur cette période."
    }


# ----- 4. CRÉER UN RDV -----

@app.post("/creer_rdv")
async def creer_rdv(
    request: CreerRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    ✅ CRÉER UN RENDEZ-VOUS

    Crée un nouveau RDV pour un patient.
    """
    date = convertir_date(request.date)
    date_naissance = convertir_date(request.date_naissance) if request.date_naissance else None
    telephone = normaliser_telephone(request.telephone)

    params = {
        "firstName": request.prenom,
        "lastName": request.nom,
        "mobile": telephone,
        "newPatient": "1" if request.nouveau_patient else "0"
    }

    if request.email:
        params["email"] = request.email
    if date_naissance:
        params["birthDate"] = date_naissance
    if request.message:
        params["messagePatient"] = request.message

    endpoint = f"/schedules/{DEFAULT_PRATICIEN_ID}/slots/{request.type_rdv}/{date}/{request.heure}/"
    result = await call_rdvdentiste("PUT", endpoint, office_code, api_key, params)

    # Vérifier le résultat
    is_confirmed = result.get("done", False)
    rdv_id = result.get("rdvId") or result.get("idDemande")
    busy_message = result.get("busy", "")

    if busy_message or (not is_confirmed and not rdv_id):
        return {
            "success": False,
            "message": "Ce créneau n'est plus disponible. Veuillez en choisir un autre."
        }

    heure_affichage = formater_heure(request.heure)

    return {
        "success": True,
        "rdv_id": rdv_id,
        "statut": "Confirmé" if is_confirmed else "En attente de confirmation",
        "date": date,
        "heure": heure_affichage,
        "patient": f"{request.prenom} {request.nom}",
        "message": f"Rendez-vous {'confirmé' if is_confirmed else 'créé'} pour le {date} à {heure_affichage}."
    }


# ----- 5. RECHERCHER UN PATIENT -----

@app.post("/rechercher_patient")
async def rechercher_patient(
    request: RechercherPatientRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    🔍 RECHERCHER UN PATIENT

    Recherche un patient par téléphone, nom, prénom ou date de naissance.
    """
    params = {}

    if request.telephone:
        params["mobile"] = normaliser_telephone(request.telephone)
    if request.nom:
        params["lastName"] = request.nom
    if request.prenom:
        params["firstName"] = request.prenom
    if request.date_naissance:
        params["birthDate"] = convertir_date(request.date_naissance)

    if not params:
        return {
            "success": False,
            "message": "Veuillez fournir au moins un critère de recherche."
        }

    result = await call_rdvdentiste("GET", "/patients/find", office_code, api_key, params, allow_404=True)

    if isinstance(result, dict) and "Error" in result:
        return {
            "success": True,
            "trouve": False,
            "message": "Aucun patient trouvé avec ces informations."
        }

    patients = []
    if isinstance(result, dict) and "Patients" in result:
        for p in result.get("Patients", []):
            patient_id = p.get("identifier") or p.get("id")
            patients.append({
                "id": patient_id,
                "nom": p.get("lastName") or p.get("family"),
                "prenom": p.get("firstName") or p.get("given"),
                "telephone": p.get("mobile")
            })

    if patients:
        return {
            "success": True,
            "trouve": True,
            "patients": patients,
            "message": f"{len(patients)} patient(s) trouvé(s)."
        }

    return {
        "success": True,
        "trouve": False,
        "message": "Aucun patient trouvé avec ces informations."
    }


# ----- 6. LISTER LES PRATICIENS ET TYPES DE RDV -----

@app.get("/praticiens")
async def lister_praticiens(
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Liste les praticiens et leurs types de RDV disponibles"""
    result = await call_rdvdentiste("GET", "/schedules", office_code, api_key)
    return {"success": True, "praticiens": result}


@app.get("/types_rdv")
async def lister_types_rdv(
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Liste tous les types de RDV disponibles"""
    result = await call_rdvdentiste("GET", "/schedules", office_code, api_key)

    types_rdv = []
    schedules = result.get("Schedules", []) if isinstance(result, dict) else result

    for schedule in schedules:
        if isinstance(schedule, dict) and "appointmentTypes" in schedule:
            for apt_type in schedule.get("appointmentTypes", []):
                types_rdv.append({
                    "code": apt_type.get("code"),
                    "nom": apt_type.get("name"),
                    "duree_minutes": apt_type.get("duration"),
                    "nouveau_patient_only": apt_type.get("newPatientOnly", False)
                })

    return {
        "success": True,
        "types_rdv": types_rdv,
        "message": f"{len(types_rdv)} types de RDV disponibles."
    }


# ============== ENDPOINTS /info/* (pour Fine-tuner.ai) ==============

@app.get("/info/types_rdv")
async def info_types_rdv(
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Liste tous les types de RDV disponibles (endpoint /info/)"""
    return await lister_types_rdv(office_code, api_key)


@app.get("/info/suggerer_type_rdv")
async def suggerer_type_rdv(
    motif: str = "",
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Suggère le type de RDV le plus adapté au motif du patient.

    Mapping des motifs vers les types de RDV courants.
    """
    motif_lower = motif.lower() if motif else ""

    # Récupérer les types disponibles
    types_result = await lister_types_rdv(office_code, api_key)
    types_rdv = types_result.get("types_rdv", [])

    # Mapping des mots-clés vers les types de RDV
    suggestions = []

    # Mots-clés pour différents types de soins
    mappings = {
        "urgence": ["urgence", "douleur", "mal", "cassé", "abcès", "gonflement", "saigne"],
        "detartrage": ["détartrage", "detartrage", "nettoyage", "tartre", "hygiène"],
        "consultation": ["consultation", "contrôle", "visite", "check", "bilan", "nouveau patient", "première visite"],
        "extraction": ["extraction", "arracher", "enlever dent", "retirer"],
        "couronne": ["couronne", "prothèse", "bridge"],
        "implant": ["implant"],
        "blanchiment": ["blanchiment", "blanchir", "éclaircissement"],
        "carie": ["carie", "cavité", "trou"],
        "devitalisation": ["dévitalisation", "devitalisation", "canal", "racine"],
    }

    # Trouver le type suggéré basé sur le motif
    type_suggere = None
    for type_key, keywords in mappings.items():
        if any(kw in motif_lower for kw in keywords):
            # Chercher un type de RDV correspondant
            for t in types_rdv:
                nom_type = (t.get("nom") or "").lower()
                if type_key in nom_type or any(kw in nom_type for kw in keywords):
                    type_suggere = t
                    break
            if type_suggere:
                break

    # Si pas de suggestion spécifique, proposer consultation générale
    if not type_suggere and types_rdv:
        for t in types_rdv:
            nom = (t.get("nom") or "").lower()
            if "consultation" in nom or "visite" in nom or "examen" in nom:
                type_suggere = t
                break
        # Sinon prendre le premier type disponible
        if not type_suggere:
            type_suggere = types_rdv[0]

    if type_suggere:
        return {
            "success": True,
            "motif": motif,
            "suggestion": type_suggere,
            "message": f"Pour '{motif}', je vous suggère un RDV de type: {type_suggere.get('nom')} (code: {type_suggere.get('code')})"
        }

    return {
        "success": False,
        "motif": motif,
        "message": "Je n'ai pas pu déterminer le type de RDV adapté. Voici les types disponibles.",
        "types_disponibles": types_rdv
    }


# ============== ENDPOINTS LEGACY (compatibilité) ==============

@app.post("/voir_rdv_patient")
async def voir_rdv_patient_legacy(
    request: VoirRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Legacy endpoint - redirige vers /voir_rdv"""
    return await voir_rdv(request, office_code, api_key)


@app.post("/consulter_disponibilites")
async def consulter_disponibilites_legacy(
    request: DisponibilitesRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Legacy endpoint - redirige vers /disponibilites"""
    return await consulter_disponibilites(request, office_code, api_key)


# ============== MAIN ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
