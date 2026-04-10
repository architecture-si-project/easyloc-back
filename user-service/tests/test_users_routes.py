import jwt

from user_app import create_app


def test_get_users_returns_401_when_token_missing():
    app = create_app()
    client = app.test_client()

    response = client.get("/users")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Missing token"}


def test_get_users_returns_401_when_token_invalid(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr(jwt, "decode", lambda token, secret, algorithms: (_ for _ in ()).throw(Exception("bad token")))

    response = client.get("/users", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid token"}


def test_get_user_returns_200_when_token_valid(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr(jwt, "decode", lambda token, secret, algorithms: {"user_id": 1})

    response = client.get("/users/42", headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 200
    assert response.get_json() == {"id": 42}

