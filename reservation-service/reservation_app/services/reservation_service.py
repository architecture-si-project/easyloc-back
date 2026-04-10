import os
from datetime import datetime

import psycopg2
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000")
HOUSING_SERVICE_URL = os.getenv("HOUSING_SERVICE_URL", "http://housing-service:5000")

ALLOWED_STATUSES = {
    "pending",
    "under_review",
    "approved",
    "rejected",
    "contract_signed",
    "active",
    "closed",
}

ALLOWED_TRANSITIONS = {
    "pending": {"under_review", "rejected"},
    "under_review": {"approved", "rejected"},
    "approved": {"contract_signed", "rejected"},
    "contract_signed": {"active", "rejected"},
    "active": {"closed"},
    "rejected": set(),
    "closed": set(),
}


def get_connection():
    # Ouvre une connexion PostgreSQL dediee a l'operation en cours.
    return psycopg2.connect(DATABASE_URL)


def _serialize_reservation_row(row):
    # Convertit une ligne SQL en dictionnaire JSON pour les routes.
    return {
        "reservation_id": row[0],
        "tenant_id": row[1],
        "housing_id": row[2],
        "start_date": str(row[3]),
        "end_date": str(row[4]),
        "status": row[5],
        "notes": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "updated_at": row[8].isoformat() if row[8] else None,
    }


def is_valid_status(status: str):
    return status in ALLOWED_STATUSES


def can_transition(current_status: str, new_status: str):
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())


def _resource_exists(url):
    # Appel HTTP court pour verifier l'existence d'une ressource distante.
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _fetch_resource(url):
    # Recupere une ressource JSON distante pour verifier des attributs metier.
    try:
        response = requests.get(url, timeout=2)
        if response.status_code != 200:
            return None
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def validate_cross_service_references(tenant_id, housing_id):
    # Verification des dependances externes pour garder une coherence inter-services.
    if not _resource_exists(f"{USER_SERVICE_URL}/users/{tenant_id}"):
        return {"error": "tenant_not_found"}

    if not _resource_exists(f"{HOUSING_SERVICE_URL}/logements/{housing_id}"):
        return {"error": "housing_not_found"}

    return None


def validate_reservation_dates(start_date, end_date):
    # Valide le format ISO (YYYY-MM-DD) et la coherence chronologique des dates.
    try:
        parsed_start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        parsed_end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return {"error": "invalid_date_format"}

    if parsed_start > parsed_end:
        return {"error": "invalid_date_range"}

    return {"start_date": parsed_start, "end_date": parsed_end}


def is_housing_available(housing_id):
    # Verifie la disponibilite globale du logement declaree par housing-service.
    housing = _fetch_resource(f"{HOUSING_SERVICE_URL}/logements/{housing_id}")
    if not housing:
        return False
    return bool(housing.get("disponible", True))


def has_overlapping_reservation(housing_id, start_date, end_date):
    # Evite le double booking sur la meme periode pour un logement.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM reservation_requests
        WHERE housing_id = %s
          AND status NOT IN (%s, %s)
          AND start_date <= %s
          AND end_date >= %s
        LIMIT 1
        """,
        (housing_id, "rejected", "closed", end_date, start_date),
    )
    overlap = cur.fetchone() is not None

    cur.close()
    conn.close()

    return overlap


def create_reservation_request(tenant_id, housing_id, start_date, end_date, notes=None):
    # Refuse la creation quand les dates ne sont pas valides.
    date_validation = validate_reservation_dates(start_date, end_date)

    if date_validation.get("error"):
        return date_validation

    parsed_start_date = date_validation["start_date"]
    parsed_end_date = date_validation["end_date"]

    # Empêche la creation si le locataire ou logement n'existe pas dans les autres services.
    validation_error = validate_cross_service_references(tenant_id, housing_id)

    if validation_error:
        return validation_error

    if not is_housing_available(housing_id):
        return {"error": "housing_not_available"}

    if has_overlapping_reservation(housing_id, parsed_start_date, parsed_end_date):
        return {"error": "overlapping_reservation"}

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO reservation_requests (tenant_id, housing_id, start_date, end_date, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING reservation_id, tenant_id, housing_id, start_date, end_date, status, notes, created_at, updated_at
        """,
        (tenant_id, housing_id, parsed_start_date, parsed_end_date, "pending", notes),
    )
    row = cur.fetchone()

    # On journalise chaque changement d'etat pour suivre le processus de location.
    cur.execute(
        """
        INSERT INTO reservation_process_events (reservation_id, old_status, new_status, actor_id, comment)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (row[0], None, "pending", tenant_id, "Reservation request created"),
    )

    conn.commit()
    cur.close()
    conn.close()

    return _serialize_reservation_row(row)


def list_reservation_requests(status=None, tenant_id=None):
    # Construit dynamiquement la requete selon les filtres fournis.
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT reservation_id, tenant_id, housing_id, start_date, end_date, status, notes, created_at, updated_at
        FROM reservation_requests
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND status = %s"
        params.append(status)

    if tenant_id is not None:
        query += " AND tenant_id = %s"
        params.append(tenant_id)

    query += " ORDER BY created_at DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [_serialize_reservation_row(row) for row in rows]


def get_reservation_request(reservation_id):
    # Lecture simple d'une demande par son identifiant.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT reservation_id, tenant_id, housing_id, start_date, end_date, status, notes, created_at, updated_at
        FROM reservation_requests
        WHERE reservation_id = %s
        """,
        (reservation_id,),
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return _serialize_reservation_row(row)


def _persist_status_transition(reservation_id, current_status, new_status, actor_id=None, comment=None):
    # Met a jour le statut puis enregistre un evenement d'audit associe.
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE reservation_requests
        SET status = %s, updated_at = NOW()
        WHERE reservation_id = %s
        RETURNING reservation_id, tenant_id, housing_id, start_date, end_date, status, notes, created_at, updated_at
        """,
        (new_status, reservation_id),
    )
    updated_row = cur.fetchone()

    cur.execute(
        """
        INSERT INTO reservation_process_events (reservation_id, old_status, new_status, actor_id, comment)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (reservation_id, current_status, new_status, actor_id, comment),
    )

    conn.commit()
    cur.close()
    conn.close()

    return _serialize_reservation_row(updated_row)


def update_reservation_status(reservation_id, new_status, actor_id=None, comment=None):
    # La validation des transitions permet de garder un workflow de location coherent.
    if not is_valid_status(new_status):
        return {"error": "invalid_status"}

    reservation = get_reservation_request(reservation_id)

    if not reservation:
        return {"error": "not_found"}

    current_status = reservation["status"]

    if not can_transition(current_status, new_status):
        return {"error": "invalid_transition", "current_status": current_status}

    updated_reservation = _persist_status_transition(
        reservation_id=reservation_id,
        current_status=current_status,
        new_status=new_status,
        actor_id=actor_id,
        comment=comment,
    )

    return {"reservation": updated_reservation}