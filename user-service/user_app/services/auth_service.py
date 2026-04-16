import datetime
import os

import bcrypt
import jwt
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def register_user(name, email, password):
    existing_user = get_user_by_email(email)

    if existing_user:
        return None

    password_hash = hash_password(password)

    user = create_user(name, email, password_hash)

    return user

def create_user(name, email, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id, name, email",
        (name, email, password),
    )

    user = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
    }

def authenticate_user(email, password):
    user = get_user_by_email(email)

    if not user:
        return None

    if not check_password(password, user[3]):
        return None

    payload = {
        "user_id": user[0],
        "exp": datetime.datetime.now() + datetime.timedelta(hours=2)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return token

def hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed_password: str):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    return user



