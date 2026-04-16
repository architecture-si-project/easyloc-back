import pytest

from user_app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_returns_400_when_fields_are_missing(client):
    response = client.post("/auth/login", json={"email": "john@example.com"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Missing required fields"}


def test_login_returns_401_when_credentials_are_invalid(client, monkeypatch):
    monkeypatch.setattr("user_app.routes.auth.authenticate_user", lambda email, password: None)

    response = client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid credentials"}


def test_login_returns_token_when_credentials_are_valid(client, monkeypatch):
    monkeypatch.setattr("user_app.routes.auth.authenticate_user", lambda email, password: "token-123")

    response = client.post(
        "/auth/login",
        json={"email": "john@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"token": "token-123"}


def test_register_returns_201_when_user_is_created(client, monkeypatch):
    monkeypatch.setattr(
        "user_app.routes.auth.register_user",
        lambda name, email, password: {"id": 1, "name": name, "email": email},
    )

    response = client.post(
        "/auth/register",
        json={"name": "John", "email": "john@example.com", "password": "secret"},
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "id": 1,
        "name": "John",
        "email": "john@example.com",
    }


def test_register_returns_409_when_user_already_exists(client, monkeypatch):
    monkeypatch.setattr("user_app.routes.auth.register_user", lambda name, email, password: None)

    response = client.post(
        "/auth/register",
        json={"name": "John", "email": "john@example.com", "password": "secret"},
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "User already exists"}

