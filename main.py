"""
Secrétaire IA - Middleware pour rdvdentiste.net / Logosw
Backend FastAPI pour Synthflow/Fine-tuner.ai Custom Actions
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
import httpx
from datetime import datetime, timedelta
import re
import os


def convertir_date(date_str: str) -> str:
    """
    Convertit une date du format français (JJ/MM/AAAA) vers ISO (YYYY-MM-DD).
    Accepte aussi le format ISO directement.
    """
    if not date_str:
        return date_str

    # Si déjà au format ISO (YYYY-MM-DD)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Format français JJ/MM/AAAA
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        jour, mois, annee = date_str.split('/')
        return f"{annee}-{mois}-{jour}"

    # Format français JJ-MM-AAAA
    if re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
        jour, mois, annee = date_str.split('-')
        return f"{annee}-{mois}-{jour}"

    # Retourner tel quel si format non reconnu
    return date_str

app = FastAPI(
    title="Secrétaire IA Dentiste",
    description="Middleware pour connecter Synthflow à l'API rdvdentiste.net",
    version="1.0.0"
)

# Configuration API rdvdentiste
RDVDENTISTE_BASE_URL = "https://www.rdvdentiste.net/api"
# Office de test - À remplacer par le vrai OfficeCode en production
DEFAULT_OFFICE_CODE = os.getenv("RDVDENTISTE_OFFICE_CODE", "0501463005IMZDB742BK")
# API Key depuis variable d'environnement
DEFAULT_API_KEY = os.getenv("RDVDENTISTE_API_KEY")


# ============== RÉFÉRENTIEL DES TYPES DE RDV ==============
# Données du cabinet dentaire

TYPES_RDV_CABINET = {
    "URGENCE": {
        "nom": "Urgence",
        "duree_minutes": 20,
        "couleur": "ROUGE",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "BILAN": {
        "nom": "Bilan CDC/Esthétique/Ortho/Paro",
        "duree_minutes": 60,
        "couleur": "BLEU FONCÉ",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "CONSULTATION": {
        "nom": "Consultation",
        "duree_minutes": 20,
        "couleur": "BLEU CLAIR",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "COLLAGE_FACETTES": {
        "nom": "Collage Facettes/Inlay/Pose",
        "duree_minutes": 30,
        "couleur": "VIOLET",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "SOINS_CONSERVATEURS": {
        "nom": "Soins Conservateurs Composites ITK",
        "duree_minutes": 30,
        "couleur": "MAUVE FONCÉ",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "DETARTRAGE": {
        "nom": "Détartrage et Maintenance",
        "duree_minutes": 40,
        "couleur": "VERT FONCÉ",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "ECLAIRCISSEMENT": {
        "nom": "Éclaircissement Fauteuil",
        "duree_minutes": 80,
        "couleur": "BLEU TRÈS CLAIR",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "PROTHESES": {
        "nom": "Prothèses Dépose/Prep/Empreinte/Provisoire",
        "duree_minutes": 60,
        "couleur": "MAUVE CLAIR",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "INLAY_IRM": {
        "nom": "Inlay IRM Empreinte Optique",
        "duree_minutes": 40,
        "couleur": "VIOLET FONCÉ",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "EVALUATION_PHOTO": {
        "nom": "Évaluation/Photo/Essayage",
        "duree_minutes": 30,
        "couleur": "VIOLET",
        "plages_horaires": {
            "Lundi": ["14h00-19h30"],
            "Mardi": ["09h30-17h00"],
            "Jeudi": ["09h30-19h30"],
            "Vendredi": ["14h00-19h30"]
        }
    },
    "LITHOTRITIE": {
        "nom": "Lithotritie",
        "duree_minutes": 40,
        "couleur": "VERT CLAIR",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"]
        }
    },
    "PROPHYLAXIE": {
        "nom": "Séance de Prophylaxie",
        "duree_minutes": 45,
        "couleur": "VERT TRÈS CLAIR",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "EXTRACTION": {
        "nom": "Extraction/Résection Apicale",
        "duree_minutes": 40,
        "couleur": "ORANGE FONCÉ",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "IMPLANT_GREFFE": {
        "nom": "Implant/Greffe",
        "duree_minutes": 45,
        "couleur": "ORANGE FONCÉ",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "RESECTION_APICALE": {
        "nom": "Résection Apicale",
        "duree_minutes": 30,
        "couleur": "ORANGE CLAIR",
        "plages_horaires": {
            "Lundi": ["09h30-14h00"],
            "Mardi": ["17h00-19h30"],
            "Jeudi": ["17h00-19h30"],
            "Vendredi": ["09h30-14h00"],
            "Samedi": ["09h00-15h00"]
        }
    },
    "INVISALIGN_1ER_RDV": {
        "nom": "Invisalign 1er RDV",
        "duree_minutes": 40,
        "couleur": "ROSE PÂLE",
        "plages_horaires": {
            "Lundi": ["18h00-19h30"],
            "Mardi": ["09h30-12h00"],
            "Jeudi": ["09h30-11h00", "18h00-19h30"],
            "Vendredi": ["18h00-19h30"]
        }
    },
    "INVISALIGN_TRAITEMENT": {
        "nom": "Invisalign Traitement",
        "duree_minutes": 40,
        "couleur": "ROSE CLAIR",
        "plages_horaires": {
            "Lundi": ["18h00-19h30"],
            "Mardi": ["09h30-12h00"],
            "Jeudi": ["09h30-11h00", "18h00-19h30"],
            "Vendredi": ["18h00-19h30"]
        }
    },
    "EMP_OPTIQUE_CONTENTION": {
        "nom": "Empreinte Optique Contention/Fil Numérique Ortho",
        "duree_minutes": 15,
        "couleur": "ROSE",
        "plages_horaires": {
            "Lundi": ["18h00-19h30"],
            "Mardi": ["09h30-12h00"],
            "Jeudi": ["09h30-11h00", "18h00-19h30"],
            "Vendredi": ["18h00-19h30"]
        }
    },
    "FIN_INVISALIGN": {
        "nom": "Fin Invisalign",
        "duree_minutes": 60,
        "couleur": "ROSE VIF",
        "plages_horaires": {
            "Lundi": ["18h00-19h30"],
            "Mardi": ["09h30-12h00"],
            "Jeudi": ["09h30-11h00", "18h00-19h30"],
            "Vendredi": ["18h00-19h30"]
        }
    }
}

# Catégories de RDV pour aider l'IA à orienter les patients
CATEGORIES_RDV = {
    "consultation_urgence_bilan": {
        "description": "Consultations, urgences et bilans",
        "types": ["URGENCE", "CONSULTATION", "BILAN"],
        "plages": "Lundi/Mardi/Jeudi/Vendredi/Samedi selon les types"
    },
    "detartrage_maintenance": {
        "description": "Détartrage, polissage et maintenance",
        "types": ["DETARTRAGE", "PROPHYLAXIE", "LITHOTRITIE"],
        "plages": "Lundi/Mardi/Vendredi/Samedi"
    },
    "facettes_protheses_empreintes": {
        "description": "Facettes, prothèses et travaux esthétiques",
        "types": ["COLLAGE_FACETTES", "PROTHESES", "INLAY_IRM", "EVALUATION_PHOTO", "SOINS_CONSERVATEURS", "ECLAIRCISSEMENT"],
        "plages": "Lundi après-midi, Mardi matin, Jeudi, Vendredi après-midi"
    },
    "chirurgie": {
        "description": "Extractions, implants et chirurgie",
        "types": ["EXTRACTION", "IMPLANT_GREFFE", "RESECTION_APICALE"],
        "plages": "Lundi/Mardi/Jeudi/Vendredi/Samedi"
    },
    "orthodontie_invisalign": {
        "description": "Orthodontie et Invisalign",
        "types": ["INVISALIGN_1ER_RDV", "INVISALIGN_TRAITEMENT", "EMP_OPTIQUE_CONTENTION", "FIN_INVISALIGN"],
        "plages": "Lundi/Mardi/Jeudi/Vendredi (créneaux spécifiques)"
    }
}


# ============== MODÈLES PYDANTIC ==============

class RechercherPatientRequest(BaseModel):
    nom: str = Field(..., description="Nom de famille du patient")
    prenom: Optional[str] = Field(None, description="Prénom du patient")
    date_naissance: Optional[str] = Field(None, description="Date de naissance (YYYY-MM-DD)")
    telephone: Optional[str] = Field(None, description="Numéro de téléphone mobile")


class ConsulterDisponibilitesRequest(BaseModel):
    praticien_id: Optional[str] = Field(None, description="ID du praticien (scheduleId)")
    type_rdv: str = Field(..., description="Type de rendez-vous")
    date_debut: str = Field(..., description="Date de début (YYYY-MM-DD)")
    date_fin: Optional[str] = Field(None, description="Date de fin (YYYY-MM-DD), max 14 jours")
    nouveau_patient: Optional[str] = Field("false", description="Est-ce un nouveau patient ? (true/false)")
    age_patient: Optional[int] = Field(None, description="Âge du patient")
    patient_id: Optional[str] = Field(None, description="ID du patient si connu")


class CreerRdvRequest(BaseModel):
    praticien_id: Optional[str] = Field("MC", description="ID du praticien (scheduleId)")
    type_rdv: str = Field(..., description="Type de rendez-vous (code numérique: 84, 27, etc.)")
    date: str = Field(..., description="Date du RDV (YYYY-MM-DD)")
    heure: str = Field(..., description="Heure du RDV (HHMM, ex: 0930)")
    nom: str = Field(..., description="Nom du patient")
    prenom: str = Field(..., description="Prénom du patient")
    telephone: str = Field(..., description="Téléphone mobile")
    email: Optional[str] = Field(None, description="Email du patient")
    date_naissance: Optional[str] = Field(None, description="Date de naissance (YYYY-MM-DD)")
    nouveau_patient: Optional[str] = Field("true", description="Est-ce un nouveau patient ? (true/false)")
    patient_id: Optional[str] = Field(None, description="ID du patient si connu")
    message: Optional[str] = Field(None, description="Message pour le praticien")


class VoirRdvPatientRequest(BaseModel):
    patient_id: str = Field(..., description="ID du patient")


class AnnulerRdvRequest(BaseModel):
    rdv_id: str = Field(..., description="ID du rendez-vous à annuler")
    praticien_id: Optional[str] = Field("MC", description="ID du praticien (scheduleId)")


# ============== HELPERS ==============

async def call_rdvdentiste(
    method: str,
    endpoint: str,
    office_code: str,
    api_key: Optional[str] = None,
    params: dict = None,
    json_data: dict = None
) -> dict:
    """Appel générique à l'API rdvdentiste"""
    # Utiliser l'API Key par défaut si non fournie
    effective_api_key = api_key or DEFAULT_API_KEY

    headers = {
        "OfficeCode": office_code,
        "Content-Type": "application/json"
    }
    if effective_api_key:
        headers["ApiKey"] = effective_api_key

    url = f"{RDVDENTISTE_BASE_URL}{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "PUT":
                response = await client.put(url, headers=headers, params=params, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                response = await client.post(url, headers=headers, params=params, json=json_data)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ============== ENDPOINTS ==============

@app.get("/")
async def root():
    """Endpoint de santé"""
    return {"status": "ok", "service": "Secrétaire IA Dentiste"}


@app.get("/debug/slots/{type_rdv}")
async def debug_slots(
    type_rdv: str,
    start: str = "2026-01-15",
    end: str = "2026-01-22",
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Debug: voir la réponse brute de l'API rdvdentiste pour les slots"""
    effective_api_key = api_key or DEFAULT_API_KEY

    # D'abord récupérer le scheduleId
    schedules_response = await call_rdvdentiste("GET", "/schedules", office_code, api_key)
    schedules = schedules_response.get("Schedules", [])
    schedule_id = schedules[0].get("id") if schedules else "unknown"

    # Construire l'URL exacte
    endpoint = f"/schedules/{schedule_id}/slots/{type_rdv}/"
    params = {"start": start, "end": end, "newPatient": "1"}

    url = f"{RDVDENTISTE_BASE_URL}{endpoint}"
    headers = {
        "OfficeCode": office_code,
        "Content-Type": "application/json"
    }
    if effective_api_key:
        headers["ApiKey"] = effective_api_key

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        return {
            "url_called": str(response.url),
            "schedule_id": schedule_id,
            "status_code": response.status_code,
            "response_raw": response.text,
            "headers_sent": {k: v for k, v in headers.items() if k != "ApiKey"}
        }


@app.get("/praticiens")
async def lister_praticiens(
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Liste les praticiens et types de RDV disponibles"""
    result = await call_rdvdentiste("GET", "/schedules", office_code, api_key)
    return {
        "success": True,
        "praticiens": result
    }


@app.post("/rechercher_patient")
async def rechercher_patient(
    request: RechercherPatientRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Recherche un patient existant dans le système.
    Retourne l'ID du patient si trouvé.
    """
    # Convertir la date de naissance si nécessaire
    date_naissance = convertir_date(request.date_naissance) if request.date_naissance else None

    params = {}
    if request.nom:
        params["lastName"] = request.nom
    if request.prenom:
        params["firstName"] = request.prenom
    if date_naissance:
        params["birthDate"] = date_naissance
    if request.telephone:
        params["mobile"] = request.telephone

    try:
        result = await call_rdvdentiste("GET", "/patients/find", office_code, api_key, params)

        # Vérifier si c'est une erreur "notFound"
        if isinstance(result, dict) and "Error" in result:
            return {
                "success": True,
                "trouve": False,
                "message": "Aucun patient trouvé avec ces informations"
            }

        if result:
            return {
                "success": True,
                "trouve": True,
                "patient": result,
                "patient_id": result.get("id"),
                "message": f"Patient trouvé avec l'ID {result.get('id', 'inconnu')}"
            }
        else:
            return {
                "success": True,
                "trouve": False,
                "message": "Aucun patient trouvé avec ces informations"
            }
    except HTTPException as e:
        # L'API retourne 404 quand le patient n'est pas trouvé
        if e.status_code == 404:
            return {
                "success": True,
                "trouve": False,
                "message": "Aucun patient trouvé avec ces informations"
            }
        raise e


@app.post("/consulter_disponibilites")
async def consulter_disponibilites(
    request: ConsulterDisponibilitesRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Consulte les créneaux disponibles pour un type de RDV.
    Retourne les créneaux libres sur la période demandée.
    """
    # Convertir les dates du format français si nécessaire
    request.date_debut = convertir_date(request.date_debut)
    if request.date_fin:
        request.date_fin = convertir_date(request.date_fin)

    # Si pas de date de fin, prendre 7 jours par défaut
    if not request.date_fin:
        date_debut = datetime.strptime(request.date_debut, "%Y-%m-%d")
        date_fin = date_debut + timedelta(days=7)
        request.date_fin = date_fin.strftime("%Y-%m-%d")

    # Si pas de praticien spécifié, récupérer la liste
    if not request.praticien_id:
        schedules_response = await call_rdvdentiste("GET", "/schedules", office_code, api_key)
        # Gérer le format FHIR de l'API rdvdentiste
        schedules = schedules_response.get("Schedules", [])
        if schedules and len(schedules) > 0:
            request.praticien_id = schedules[0].get("id")
        else:
            raise HTTPException(status_code=404, detail="Aucun praticien trouvé")

    # Convertir nouveau_patient string en boolean
    is_new_patient = request.nouveau_patient and request.nouveau_patient.lower() == "true"

    params = {
        "start": request.date_debut,
        "end": request.date_fin,
        "newPatient": "1" if is_new_patient else "0"
    }
    if request.age_patient:
        params["patientAge"] = request.age_patient
    if request.patient_id:
        params["patientId"] = request.patient_id

    endpoint = f"/schedules/{request.praticien_id}/slots/{request.type_rdv}/"
    result = await call_rdvdentiste("GET", endpoint, office_code, api_key, params)

    # Formater les créneaux pour une réponse claire
    creneaux_formates = []
    # L'API retourne un objet avec "AvailableSlots" contenant la liste des créneaux
    slots = result.get("AvailableSlots", []) if isinstance(result, dict) else result
    for slot in slots:
        # Extraire date et heure depuis le format ISO "2026-01-17T11:40:00"
        start_time = slot.get("start", "")
        if start_time:
            date_part = start_time.split("T")[0]  # "2026-01-17"
            time_part = start_time.split("T")[1][:5].replace(":", "")  # "1140"
            creneaux_formates.append({
                "date": date_part,
                "heure": time_part,
                "heure_format": start_time.split("T")[1][:5],  # "11:40"
                "disponible": True
            })

    return {
        "success": True,
        "periode": f"Du {request.date_debut} au {request.date_fin}",
        "type_rdv": request.type_rdv,
        "creneaux": creneaux_formates,
        "nombre_creneaux": len(creneaux_formates),
        "message": f"{len(creneaux_formates)} créneaux disponibles" if creneaux_formates else "Aucun créneau disponible sur cette période"
    }


@app.post("/creer_rdv")
async def creer_rdv(
    request: CreerRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Crée un nouveau rendez-vous.
    Le RDV sera en attente de confirmation par le praticien.
    """
    # Si pas de praticien_id, récupérer automatiquement
    if not request.praticien_id:
        schedules_response = await call_rdvdentiste("GET", "/schedules", office_code, api_key)
        schedules = schedules_response.get("Schedules", [])
        if schedules and len(schedules) > 0:
            request.praticien_id = schedules[0].get("id")
        else:
            request.praticien_id = "MC"  # Fallback

    # Convertir les dates du format français si nécessaire
    request.date = convertir_date(request.date)
    if request.date_naissance:
        request.date_naissance = convertir_date(request.date_naissance)

    # Convertir nouveau_patient string en boolean
    is_new_patient = request.nouveau_patient and request.nouveau_patient.lower() == "true"

    params = {
        "firstName": request.prenom,
        "lastName": request.nom,
        "mobile": request.telephone,
        "newPatient": "1" if is_new_patient else "0"
    }
    if request.email:
        params["email"] = request.email
    if request.date_naissance:
        params["birthDate"] = request.date_naissance
    if request.patient_id:
        params["patientId"] = request.patient_id
    if request.message:
        params["messagePatient"] = request.message

    endpoint = f"/schedules/{request.praticien_id}/slots/{request.type_rdv}/{request.date}/{request.heure}/"
    result = await call_rdvdentiste("PUT", endpoint, office_code, api_key, params)

    # Vérifier si le RDV est confirmé directement
    is_confirmed = result.get("done", False)
    rdv_id = result.get("rdvId") or result.get("idDemande")

    # Vérifier si le créneau n'est plus disponible
    busy_message = result.get("busy", "")
    if busy_message or (not is_confirmed and not rdv_id):
        return {
            "success": False,
            "erreur": "creneau_indisponible",
            "message": "Ce créneau n'est plus disponible. Veuillez consulter les disponibilités à nouveau et choisir un autre créneau.",
            "details": result
        }

    return {
        "success": True,
        "rdv_id": rdv_id,
        "statut": "Confirmé" if is_confirmed else "En attente de confirmation",
        "message": f"Rendez-vous confirmé pour {request.prenom} {request.nom} le {request.date} à {request.heure[:2]}h{request.heure[2:]}." if is_confirmed else f"Rendez-vous créé pour {request.prenom} {request.nom}, en attente de confirmation.",
        "details": result
    }


@app.post("/voir_rdv_patient")
async def voir_rdv_patient(
    request: VoirRdvPatientRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Affiche tous les rendez-vous d'un patient.
    """
    endpoint = f"/patients/{request.patient_id}/appointments"
    result = await call_rdvdentiste("GET", endpoint, office_code, api_key)

    rdvs_formates = []
    if isinstance(result, list):
        for rdv in result:
            rdvs_formates.append({
                "id": rdv.get("id"),
                "date": rdv.get("date"),
                "heure": rdv.get("hour"),
                "type": rdv.get("type"),
                "praticien": rdv.get("practitioner"),
                "statut": rdv.get("status", "Confirmé")
            })

    return {
        "success": True,
        "patient_id": request.patient_id,
        "rdvs": rdvs_formates,
        "nombre_rdvs": len(rdvs_formates),
        "message": f"Le patient a {len(rdvs_formates)} rendez-vous" if rdvs_formates else "Aucun rendez-vous trouvé pour ce patient"
    }


@app.post("/annuler_rdv")
async def annuler_rdv(
    request: AnnulerRdvRequest,
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """
    Annule un rendez-vous existant.
    L'ID peut être au format D123456 (appointment) ou juste 123456 (request).
    """
    praticien_id = request.praticien_id or "MC"
    rdv_id = request.rdv_id

    # Si l'ID commence par D, c'est un appointment confirmé
    # Sinon c'est une demande (request)
    if rdv_id.startswith("D"):
        endpoint = f"/schedules/{praticien_id}/appointments/{rdv_id}"
    else:
        endpoint = f"/schedules/{praticien_id}/appointment-requests/{rdv_id}"

    try:
        result = await call_rdvdentiste("DELETE", endpoint, office_code, api_key)
        return {
            "success": True,
            "rdv_id": request.rdv_id,
            "message": f"Le rendez-vous {request.rdv_id} a été annulé avec succès",
            "details": result
        }
    except HTTPException as e:
        # Si erreur, essayer l'autre endpoint
        if rdv_id.startswith("D"):
            alt_endpoint = f"/schedules/{praticien_id}/appointment-requests/{rdv_id[1:]}"
        else:
            alt_endpoint = f"/schedules/{praticien_id}/appointments/D{rdv_id}"

        try:
            result = await call_rdvdentiste("DELETE", alt_endpoint, office_code, api_key)
            return {
                "success": True,
                "rdv_id": request.rdv_id,
                "message": f"Le rendez-vous {request.rdv_id} a été annulé avec succès",
                "details": result
            }
        except:
            raise e


# ============== ENDPOINT POUR TYPES DE RDV ==============

@app.get("/types_rdv")
async def lister_types_rdv(
    office_code: str = Header(default=DEFAULT_OFFICE_CODE, alias="X-Office-Code"),
    api_key: Optional[str] = Header(default=None, alias="X-Api-Key")
):
    """Liste tous les types de rendez-vous disponibles depuis l'API"""
    result = await call_rdvdentiste("GET", "/schedules", office_code, api_key)

    types_rdv = []
    if isinstance(result, list):
        for schedule in result:
            if "appointmentTypes" in schedule:
                for apt_type in schedule["appointmentTypes"]:
                    types_rdv.append({
                        "code": apt_type.get("code"),
                        "nom": apt_type.get("name"),
                        "duree": apt_type.get("duration"),
                        "praticien_id": schedule.get("id"),
                        "praticien_nom": schedule.get("name"),
                        "nouveau_patient_only": apt_type.get("newPatientOnly", False),
                        "patient_existant_only": apt_type.get("existingPatientOnly", False),
                        "instructions": apt_type.get("instructions")
                    })

    return {
        "success": True,
        "types_rdv": types_rdv,
        "message": f"{len(types_rdv)} types de rendez-vous disponibles"
    }


# ============== ENDPOINTS INFORMATIONS CABINET ==============

@app.get("/info/types_rdv")
async def info_types_rdv():
    """
    Retourne les informations détaillées sur tous les types de RDV du cabinet.
    Inclut les durées et les plages horaires.
    Utiliser cette action pour informer le patient sur les types de RDV disponibles.
    """
    types_formates = []
    for code, info in TYPES_RDV_CABINET.items():
        jours_disponibles = list(info["plages_horaires"].keys())
        types_formates.append({
            "code": code,
            "nom": info["nom"],
            "duree_minutes": info["duree_minutes"],
            "jours_disponibles": jours_disponibles,
            "plages_horaires": info["plages_horaires"]
        })

    return {
        "success": True,
        "types_rdv": types_formates,
        "message": f"Le cabinet propose {len(types_formates)} types de rendez-vous"
    }


@app.get("/info/categories")
async def info_categories():
    """
    Retourne les catégories de RDV pour aider à orienter les patients.
    Utile quand le patient ne sait pas quel type de RDV choisir.
    """
    categories_formates = []
    for code, info in CATEGORIES_RDV.items():
        categories_formates.append({
            "categorie": code,
            "description": info["description"],
            "types_inclus": info["types"],
            "plages_generales": info["plages"]
        })

    return {
        "success": True,
        "categories": categories_formates,
        "message": "Utilisez ces catégories pour orienter le patient vers le bon type de RDV"
    }


@app.get("/info/horaires")
async def info_horaires():
    """
    Retourne les horaires généraux du cabinet par jour.
    """
    horaires = {
        "Lundi": {
            "ouverture": "09h30",
            "fermeture": "19h30",
            "types_matin": ["Consultation", "Urgence", "Bilan", "Détartrage", "Chirurgie"],
            "types_apres_midi": ["Facettes", "Prothèses", "Soins esthétiques"],
            "types_soir": ["Invisalign/Orthodontie (18h00-19h30)"]
        },
        "Mardi": {
            "ouverture": "09h30",
            "fermeture": "19h30",
            "types_matin": ["Facettes", "Prothèses", "Soins esthétiques", "Invisalign"],
            "types_soir": ["Consultation", "Urgence", "Détartrage", "Chirurgie (17h00-19h30)"]
        },
        "Mercredi": {
            "ouverture": None,
            "fermeture": None,
            "note": "Cabinet fermé"
        },
        "Jeudi": {
            "ouverture": "09h30",
            "fermeture": "19h30",
            "types_matin": ["Facettes", "Prothèses", "Invisalign"],
            "types_soir": ["Consultation", "Urgence", "Chirurgie (17h00-19h30)"],
            "types_journee": ["Travaux esthétiques"]
        },
        "Vendredi": {
            "ouverture": "09h30",
            "fermeture": "19h30",
            "types_matin": ["Consultation", "Urgence", "Détartrage", "Chirurgie"],
            "types_apres_midi": ["Facettes", "Prothèses", "Soins esthétiques"],
            "types_soir": ["Invisalign (18h00-19h30)"]
        },
        "Samedi": {
            "ouverture": "09h00",
            "fermeture": "15h00",
            "types": ["Consultation", "Urgence", "Détartrage", "Chirurgie"]
        },
        "Dimanche": {
            "ouverture": None,
            "fermeture": None,
            "note": "Cabinet fermé"
        }
    }

    return {
        "success": True,
        "horaires": horaires,
        "message": "Horaires du cabinet dentaire"
    }


@app.post("/info/suggerer_type_rdv")
async def suggerer_type_rdv(motif: str = ""):
    """
    Suggère un type de RDV basé sur le motif du patient.
    Utiliser cette action quand le patient décrit son problème mais ne sait pas quel RDV prendre.
    """
    motif_lower = motif.lower()

    suggestions = []

    # Urgences
    if any(mot in motif_lower for mot in ["mal", "douleur", "urgent", "urgence", "cassé", "tombé", "gonflé", "abcès"]):
        suggestions.append({
            "code": "URGENCE",
            "nom": "Urgence",
            "raison": "Douleur ou problème nécessitant une prise en charge rapide",
            "duree": "20 min"
        })

    # Détartrage
    if any(mot in motif_lower for mot in ["détartrage", "nettoyage", "tartre", "gencives", "saignement"]):
        suggestions.append({
            "code": "DETARTRAGE",
            "nom": "Détartrage et Maintenance",
            "raison": "Nettoyage professionnel des dents",
            "duree": "40 min"
        })

    # Consultation / Contrôle
    if any(mot in motif_lower for mot in ["contrôle", "visite", "consultation", "premier", "nouveau", "avis"]):
        suggestions.append({
            "code": "CONSULTATION",
            "nom": "Consultation",
            "raison": "Premier rendez-vous ou contrôle de routine",
            "duree": "20 min"
        })

    # Bilan complet
    if any(mot in motif_lower for mot in ["bilan", "complet", "esthétique", "sourire", "parodont"]):
        suggestions.append({
            "code": "BILAN",
            "nom": "Bilan CDC/Esthétique/Ortho/Paro",
            "raison": "Évaluation complète de la situation dentaire",
            "duree": "60 min"
        })

    # Blanchiment
    if any(mot in motif_lower for mot in ["blanchiment", "éclaircissement", "blanc", "jaune"]):
        suggestions.append({
            "code": "ECLAIRCISSEMENT",
            "nom": "Éclaircissement Fauteuil",
            "raison": "Blanchiment dentaire professionnel",
            "duree": "80 min"
        })

    # Invisalign / Orthodontie
    if any(mot in motif_lower for mot in ["invisalign", "alignement", "aligneur", "orthodontie", "dents de travers"]):
        suggestions.append({
            "code": "INVISALIGN_1ER_RDV",
            "nom": "Invisalign 1er RDV",
            "raison": "Consultation pour traitement d'alignement invisible",
            "duree": "40 min"
        })

    # Implant
    if any(mot in motif_lower for mot in ["implant", "greffe", "manque une dent", "remplacer"]):
        suggestions.append({
            "code": "IMPLANT_GREFFE",
            "nom": "Implant/Greffe",
            "raison": "Remplacement d'une dent manquante",
            "duree": "45 min"
        })

    # Extraction
    if any(mot in motif_lower for mot in ["extraction", "arracher", "enlever", "sagesse"]):
        suggestions.append({
            "code": "EXTRACTION",
            "nom": "Extraction/Résection Apicale",
            "raison": "Extraction dentaire",
            "duree": "40 min"
        })

    # Prothèses / Couronnes
    if any(mot in motif_lower for mot in ["prothèse", "couronne", "bridge", "dentier"]):
        suggestions.append({
            "code": "PROTHESES",
            "nom": "Prothèses",
            "raison": "Travaux de prothèse dentaire",
            "duree": "60 min"
        })

    # Facettes
    if any(mot in motif_lower for mot in ["facette", "esthétique", "sourire"]):
        suggestions.append({
            "code": "COLLAGE_FACETTES",
            "nom": "Collage Facettes/Inlay/Pose",
            "raison": "Travaux esthétiques",
            "duree": "30 min"
        })

    # Si aucune suggestion, proposer une consultation
    if not suggestions:
        suggestions.append({
            "code": "CONSULTATION",
            "nom": "Consultation",
            "raison": "Pour évaluer votre situation et vous orienter",
            "duree": "20 min"
        })

    return {
        "success": True,
        "motif_patient": motif,
        "suggestions": suggestions,
        "message": f"{len(suggestions)} type(s) de RDV suggéré(s) pour ce motif"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
