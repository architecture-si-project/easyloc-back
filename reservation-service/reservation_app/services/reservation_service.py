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
    # Open a dedicated PostgreSQL connection for the current operation.
    return psycopg2.connect(DATABASE_URL)


def _serialize_reservation_row(row):
    # Convert a SQL row into a JSON-friendly dictionary for the routes.
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


def _resource_exists(url, headers=None):
    # Make a short HTTP call to verify that a remote resource exists.
    try:
        response = requests.get(url, timeout=2, headers=headers)
        return response.status_code == 200
    except requests.RequestException:
        return False


def _fetch_resource(url, headers=None):
    # Fetch a remote JSON resource to validate business attributes.
    try:
        response = requests.get(url, timeout=2, headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def _build_auth_headers(auth_token=None):
    if not auth_token:
        return None
    return {"Authorization": f"Bearer {auth_token}"}


def validate_cross_service_references(tenant_id, housing_id, auth_token=None):
    # Check external dependencies to keep the services consistent.
    headers = _build_auth_headers(auth_token)

    if headers:
        tenant_exists = _resource_exists(f"{USER_SERVICE_URL}/users/{tenant_id}", headers=headers)
    else:
        tenant_exists = _resource_exists(f"{USER_SERVICE_URL}/users/{tenant_id}")

    if not tenant_exists:
        return {"error": "tenant_not_found"}

    if headers:
        housing_exists = _resource_exists(f"{HOUSING_SERVICE_URL}/housing/{housing_id}", headers=headers)
    else:
        housing_exists = _resource_exists(f"{HOUSING_SERVICE_URL}/housing/{housing_id}")

    if not housing_exists:
        return {"error": "housing_not_found"}

    return None


def validate_reservation_dates(start_date, end_date):
    # Validate the ISO format (YYYY-MM-DD) and the chronological order of dates.
    try:
        parsed_start = datetime.strptime(str(start_date), "%Y-%m-%d").date()
        parsed_end = datetime.strptime(str(end_date), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return {"error": "invalid_date_format"}

    if parsed_start > parsed_end:
        return {"error": "invalid_date_range"}

    return {"start_date": parsed_start, "end_date": parsed_end}


def is_housing_available(housing_id, auth_token=None):
    # Check whether the housing unit is currently available in housing-service.
    headers = _build_auth_headers(auth_token)
    if headers:
        housing = _fetch_resource(f"{HOUSING_SERVICE_URL}/housing/{housing_id}", headers=headers)
    else:
        housing = _fetch_resource(f"{HOUSING_SERVICE_URL}/housing/{housing_id}")

    if not housing:
        return False
    return bool(housing.get("available", True))


def has_overlapping_reservation(housing_id, start_date, end_date):
    # Prevent double booking for the same housing unit during the same period.
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


def create_reservation_request(tenant_id, housing_id, start_date, end_date, notes=None, auth_token=None):
    # Reject creation when the dates are invalid.
    date_validation = validate_reservation_dates(start_date, end_date)

    if date_validation.get("error"):
        return date_validation

    parsed_start_date = date_validation["start_date"]
    parsed_end_date = date_validation["end_date"]

    # Prevent creation if the tenant or housing unit does not exist in the other services.
    if auth_token:
        validation_error = validate_cross_service_references(tenant_id, housing_id, auth_token)
    else:
        validation_error = validate_cross_service_references(tenant_id, housing_id)

    if validation_error:
        return validation_error

    if auth_token:
        housing_available = is_housing_available(housing_id, auth_token)
    else:
        housing_available = is_housing_available(housing_id)

    if not housing_available:
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

    # Log each state change to track the rental process.
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
    # Build the query dynamically based on the provided filters.
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
    # Simple read of a request by its identifier.
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
    # Update the status and record an associated audit event.
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
    # Transition validation keeps the rental workflow consistent.
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