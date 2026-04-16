import pytest

from housing_app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(monkeypatch):
    monkeypatch.setattr("housing_app.routes.housing.jwt.decode", lambda token, secret, algorithms: {"user_id": 1})
    return {"Authorization": "Bearer test-token"}


def test_get_housing_requires_token(client):
    response = client.get("/housing")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Missing token"}


def test_get_housing_returns_empty_list(client, monkeypatch, auth_headers):
    monkeypatch.setattr("housing_app.routes.housing.get_all", lambda: [])

    response = client.get("/housing", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_housing_returns_201(client, monkeypatch, auth_headers):
    payload = {
        "title": "Studio Lyon",
        "property_type": "studio",
        "location": "Lyon",
        "price_per_night": 50.0,
        "owner_id": 1,
    }
    monkeypatch.setattr(
        "housing_app.routes.housing.create",
        lambda data: {"id": 1, **data, "available": True, "created_at": None, "updated_at": None},
    )

    response = client.post("/housing", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "Studio Lyon"


def test_create_housing_returns_400_when_fields_missing(client, auth_headers):
    response = client.post("/housing", json={"title": "Incomplete"}, headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "location" in data["error"]
    assert "price_per_night" in data["error"]


def test_create_housing_returns_400_when_required_field_is_null(client, auth_headers):
    payload = {
        "title": None,
        "property_type": "studio",
        "location": "Lyon",
        "price_per_night": 50.0,
        "owner_id": 1,
    }
    response = client.post("/housing", json=payload, headers=auth_headers)

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "title" in data["error"]


def test_create_housing_returns_400_when_string_field_is_empty(client, auth_headers):
    for empty_field in ("title", "property_type", "location"):
        payload = {
            "title": "Studio Lyon",
            "property_type": "studio",
            "location": "Lyon",
            "price_per_night": 50.0,
            "owner_id": 1,
            empty_field: "  ",
        }
        response = client.post("/housing", json=payload, headers=auth_headers)

        assert response.status_code == 400, f"Expected 400 for empty {empty_field}"
        data = response.get_json()
        assert "error" in data
        assert empty_field in data["error"]


def test_get_housing_by_id_returns_404_when_missing(client, monkeypatch, auth_headers):
    monkeypatch.setattr("housing_app.routes.housing.get_by_id", lambda housing_id: None)

    response = client.get("/housing/999", headers=auth_headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Housing not found"}


def test_search_housing_returns_filtered_items(client, monkeypatch, auth_headers):
    monkeypatch.setattr(
        "housing_app.routes.housing.search",
        lambda location, property_type, price_max, owner_id: [
            {
                "id": 1,
                "title": "Maison Bordeaux",
                "property_type": "house",
                "location": "Bordeaux",
                "price_per_night": 120.0,
                "owner_id": 1,
                "available": True,
                "created_at": None,
                "updated_at": None,
            }
        ],
    )

    response = client.get("/housing/search?location=bordeaux", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_update_housing_returns_200(client, monkeypatch, auth_headers):
    monkeypatch.setattr(
        "housing_app.routes.housing.update",
        lambda housing_id, data: {"id": housing_id, "title": data.get("title", "Old")},
    )

    response = client.put("/housing/1", json={"title": "New"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["title"] == "New"


def test_delete_housing_returns_200(client, monkeypatch, auth_headers):
    monkeypatch.setattr("housing_app.routes.housing.delete", lambda housing_id: True)

    response = client.delete("/housing/1", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Housing deleted"}
