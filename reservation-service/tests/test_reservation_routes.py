import pytest

from reservation_app import create_app


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
    monkeypatch.setattr("reservation_app.routes.reservations.jwt.decode", lambda token, secret, algorithms: {"user_id": 1})
    return {"Authorization": "Bearer test-token"}


def test_create_request_returns_401_when_token_is_missing(client):
    response = client.post("/reservations/requests", json={"housing_id": 1})

    assert response.status_code == 401
    assert response.get_json() == {"error": "Missing token"}


def test_create_request_returns_401_when_token_payload_is_missing_user_id(client, monkeypatch):
    monkeypatch.setattr(
        "reservation_app.routes.reservations.jwt.decode",
        lambda token, secret, algorithms: {"sub": "abc"},
    )
    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid token"}


def test_create_request_returns_400_when_fields_are_missing(client, auth_headers):
    response = client.post("/reservations/requests", json={"housing_id": 22}, headers=auth_headers)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Missing required fields"}


def test_create_request_returns_201_when_request_is_created(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {
            "reservation_id": 1,
            "tenant_id": tenant_id,
            "housing_id": housing_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "pending",
            "notes": notes,
            "created_at": "2026-04-10T10:00:00+00:00",
            "updated_at": "2026-04-10T10:00:00+00:00",
        },
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "notes": "Need furnished place",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.get_json()["status"] == "pending"


def test_create_request_forwards_auth_token_to_service(client, monkeypatch, auth_headers):
    captured = {}

    def fake_create_reservation_request(tenant_id, housing_id, start_date, end_date, notes, auth_token=None):
        captured["auth_token"] = auth_token
        return {
            "reservation_id": 2,
            "tenant_id": tenant_id,
            "housing_id": housing_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "pending",
            "notes": notes,
            "created_at": "2026-04-10T10:00:00+00:00",
            "updated_at": "2026-04-10T10:00:00+00:00",
        }

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        fake_create_reservation_request,
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "notes": "Need furnished place",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert captured["auth_token"] == "test-token"


def test_list_my_requests_returns_401_when_token_is_missing(client):
    response = client.get("/reservations/requests/me")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Missing token"}


def test_list_my_requests_filters_by_current_user(client, monkeypatch, auth_headers):
    captured = {}

    def fake_list_reservation_requests(status=None, tenant_id=None):
        captured["status"] = status
        captured["tenant_id"] = tenant_id
        return [{"reservation_id": 1, "tenant_id": tenant_id, "status": "pending"}]

    monkeypatch.setattr(
        "reservation_app.routes.reservations.list_reservation_requests",
        fake_list_reservation_requests,
    )

    response = client.get("/reservations/requests/me?status=pending", headers=auth_headers)

    assert response.status_code == 200
    assert captured["tenant_id"] == 1
    assert captured["status"] == "pending"
    assert response.get_json()[0]["tenant_id"] == 1


def test_create_request_returns_404_when_tenant_is_missing_in_user_service(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "tenant_not_found"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Tenant not found in user-service"}


def test_create_request_returns_404_when_housing_is_missing_in_housing_service(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "housing_not_found"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 999,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Housing not found in housing-service"}


def test_create_request_returns_400_when_date_format_is_invalid(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "invalid_date_format"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "01-05-2026",
            "end_date": "31-05-2026",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Dates must follow YYYY-MM-DD format"}


def test_create_request_returns_400_when_date_range_is_invalid(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "invalid_date_range"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-06-01",
            "end_date": "2026-05-01",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "start_date must be before or equal to end_date"}


def test_create_request_returns_409_when_housing_is_marked_unavailable(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "housing_not_available"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Housing is currently unavailable"}


def test_create_request_returns_409_when_period_overlaps(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.create_reservation_request",
        lambda tenant_id, housing_id, start_date, end_date, notes, auth_token=None: {"error": "overlapping_reservation"},
    )

    response = client.post(
        "/reservations/requests",
        json={
            "housing_id": 22,
            "start_date": "2026-05-15",
            "end_date": "2026-05-25",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Housing is not available on the requested period"}


def test_get_request_returns_404_when_reservation_does_not_exist(client, monkeypatch, auth_headers):

    monkeypatch.setattr("reservation_app.routes.reservations.get_reservation_request", lambda reservation_id: None)

    response = client.get("/reservations/requests/999", headers=auth_headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Reservation request not found"}


def test_patch_request_status_returns_409_for_invalid_transition(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.update_reservation_status",
        lambda reservation_id, new_status, actor_id, comment: {
            "error": "invalid_transition",
            "current_status": "pending",
        },
    )

    response = client.patch(
        "/reservations/requests/1/status",
        json={"status": "active", "actor_id": 7, "comment": "Skipping steps"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "Invalid status transition",
        "from": "pending",
        "to": "active",
    }


def test_patch_request_status_returns_200_when_valid(client, monkeypatch, auth_headers):

    monkeypatch.setattr(
        "reservation_app.routes.reservations.update_reservation_status",
        lambda reservation_id, new_status, actor_id, comment: {
            "reservation": {
                "reservation_id": reservation_id,
                "status": new_status,
                "updated_at": "2026-04-10T12:00:00+00:00",
            }
        },
    )

    response = client.patch(
        "/reservations/requests/1/status",
        json={"status": "under_review", "actor_id": 7, "comment": "Documents validated"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "under_review"