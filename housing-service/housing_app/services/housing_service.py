import os

import psycopg2


DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def _serialize_housing_row(row):
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "property_type": row[3],
        "location": row[4],
        "price_per_night": row[5],
        "available": row[6],
        "owner_id": row[7],
        "created_at": row[8].isoformat() if row[8] else None,
        "updated_at": row[9].isoformat() if row[9] else None,
    }


def get_all():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        FROM housing
        ORDER BY created_at DESC, id DESC
        """
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [_serialize_housing_row(row) for row in rows]


def get_by_id(housing_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        FROM housing
        WHERE id = %s
        """,
        (housing_id,),
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return _serialize_housing_row(row)


def get_by_owner(owner_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        FROM housing
        WHERE owner_id = %s
        ORDER BY created_at DESC, id DESC
        """,
        (owner_id,),
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [_serialize_housing_row(row) for row in rows]


def search(location=None, property_type=None, price_max=None, owner_id=None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        FROM housing
        WHERE 1=1
    """
    params = []

    if location:
        query += " AND location ILIKE %s"
        params.append(f"%{location}%")

    if property_type:
        query += " AND property_type = %s"
        params.append(property_type)

    if price_max is not None:
        query += " AND price_per_night <= %s"
        params.append(price_max)

    if owner_id is not None:
        query += " AND owner_id = %s"
        params.append(owner_id)

    query += " ORDER BY created_at DESC, id DESC"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [_serialize_housing_row(row) for row in rows]


def create(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO housing (title, description, property_type, location, price_per_night, available, owner_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        """,
        (
            data["title"],
            data.get("description", ""),
            data["property_type"],
            data["location"],
            data["price_per_night"],
            data.get("available", True),
            data["owner_id"],
        ),
    )
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return _serialize_housing_row(row)


def update(housing_id, data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE housing
        SET title = COALESCE(%s, title),
            description = COALESCE(%s, description),
            property_type = COALESCE(%s, property_type),
            location = COALESCE(%s, location),
            price_per_night = COALESCE(%s, price_per_night),
            available = COALESCE(%s, available),
            owner_id = COALESCE(%s, owner_id),
            updated_at = NOW()
        WHERE id = %s
        RETURNING id, title, description, property_type, location, price_per_night, available, owner_id, created_at, updated_at
        """,
        (
            data.get("title"),
            data.get("description"),
            data.get("property_type"),
            data.get("location"),
            data.get("price_per_night"),
            data.get("available"),
            data.get("owner_id"),
            housing_id,
        ),
    )
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return _serialize_housing_row(row)


def delete(housing_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM housing WHERE id = %s RETURNING id", (housing_id,))
    row = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return row is not None

