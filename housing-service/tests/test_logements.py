import pytest
from app import create_app, db


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_logements_vide(client):
    r = client.get("/logements")
    assert r.status_code == 200
    assert r.get_json() == []


def test_create_logement(client):
    payload = {
        "titre": "Studio Lyon",
        "type": "studio",
        "localisation": "Lyon",
        "prix_par_nuit": 50.0,
        "proprietaire_id": 1,
    }
    r = client.post("/logements", json=payload)
    assert r.status_code == 201
    data = r.get_json()
    assert data["titre"] == "Studio Lyon"
    assert data["id"] is not None


def test_create_logement_champs_manquants(client):
    r = client.post("/logements", json={"titre": "Incomplet"})
    assert r.status_code == 400


def test_get_logement_par_id(client):
    client.post("/logements", json={
        "titre": "Appart Paris",
        "type": "appartement",
        "localisation": "Paris",
        "prix_par_nuit": 80.0,
        "proprietaire_id": 2,
    })
    r = client.get("/logements/1")
    assert r.status_code == 200
    assert r.get_json()["localisation"] == "Paris"


def test_get_logement_inexistant(client):
    r = client.get("/logements/999")
    assert r.status_code == 404


def test_search_logements(client):
    client.post("/logements", json={
        "titre": "Maison Bordeaux",
        "type": "maison",
        "localisation": "Bordeaux",
        "prix_par_nuit": 120.0,
        "proprietaire_id": 1,
    })
    r = client.get("/logements/search?localisation=bordeaux")
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_update_logement(client):
    client.post("/logements", json={
        "titre": "Old",
        "type": "studio",
        "localisation": "Nice",
        "prix_par_nuit": 30.0,
        "proprietaire_id": 1,
    })
    r = client.put("/logements/1", json={"titre": "New", "prix_par_nuit": 40.0})
    assert r.status_code == 200
    assert r.get_json()["titre"] == "New"


def test_delete_logement(client):
    client.post("/logements", json={
        "titre": "A supprimer",
        "type": "studio",
        "localisation": "Marseille",
        "prix_par_nuit": 25.0,
        "proprietaire_id": 1,
    })
    r = client.delete("/logements/1")
    assert r.status_code == 200
    assert client.get("/logements/1").status_code == 404
