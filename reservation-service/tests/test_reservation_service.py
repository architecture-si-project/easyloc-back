from reservation_app.services import reservation_service


def test_is_valid_status_returns_true_for_supported_status():
    assert reservation_service.is_valid_status("pending") is True
    assert reservation_service.is_valid_status("closed") is True


def test_is_valid_status_returns_false_for_unknown_status():
    assert reservation_service.is_valid_status("unknown") is False


def test_validate_reservation_dates_rejects_invalid_format():
    result = reservation_service.validate_reservation_dates("01-05-2026", "31-05-2026")

    assert result == {"error": "invalid_date_format"}


def test_validate_reservation_dates_rejects_invalid_range():
    result = reservation_service.validate_reservation_dates("2026-06-01", "2026-05-01")

    assert result == {"error": "invalid_date_range"}


def test_validate_reservation_dates_accepts_valid_range():
    result = reservation_service.validate_reservation_dates("2026-05-01", "2026-05-31")

    assert result["start_date"].isoformat() == "2026-05-01"
    assert result["end_date"].isoformat() == "2026-05-31"


def test_can_transition_validates_workflow_rules():
    assert reservation_service.can_transition("pending", "under_review") is True
    assert reservation_service.can_transition("pending", "active") is False


def test_update_reservation_status_returns_error_for_invalid_status():
    result = reservation_service.update_reservation_status(1, "INVALID")

    assert result == {"error": "invalid_status"}


def test_update_reservation_status_returns_error_when_reservation_is_missing(monkeypatch):
    monkeypatch.setattr(reservation_service, "get_reservation_request", lambda reservation_id: None)

    result = reservation_service.update_reservation_status(1, "under_review")

    assert result == {"error": "not_found"}


def test_update_reservation_status_returns_error_for_invalid_transition(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "get_reservation_request",
        lambda reservation_id: {"reservation_id": 1, "status": "pending"},
    )

    result = reservation_service.update_reservation_status(1, "active")

    assert result == {"error": "invalid_transition", "current_status": "pending"}


def test_update_reservation_status_calls_persistence_for_valid_transition(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "get_reservation_request",
        lambda reservation_id: {"reservation_id": 1, "status": "pending"},
    )

    def fake_persist_status_transition(reservation_id, current_status, new_status, actor_id, comment):
        assert reservation_id == 1
        assert current_status == "pending"
        assert new_status == "under_review"
        assert actor_id == 4
        assert comment == "Folder complete"
        return {
            "reservation_id": reservation_id,
            "status": new_status,
            "updated_at": "2026-04-10T12:30:00+00:00",
        }

    monkeypatch.setattr(reservation_service, "_persist_status_transition", fake_persist_status_transition)

    result = reservation_service.update_reservation_status(
        reservation_id=1,
        new_status="under_review",
        actor_id=4,
        comment="Folder complete",
    )

    assert result == {
        "reservation": {
            "reservation_id": 1,
            "status": "under_review",
            "updated_at": "2026-04-10T12:30:00+00:00",
        }
    }


def test_validate_cross_service_references_returns_tenant_not_found(monkeypatch):
    monkeypatch.setattr(reservation_service, "_resource_exists", lambda url: False)

    result = reservation_service.validate_cross_service_references(tenant_id=99, housing_id=1)

    assert result == {"error": "tenant_not_found"}


def test_validate_cross_service_references_returns_none_when_all_exist(monkeypatch):
    monkeypatch.setattr(reservation_service, "_resource_exists", lambda url: True)

    result = reservation_service.validate_cross_service_references(tenant_id=1, housing_id=2)

    assert result is None


def test_validate_cross_service_references_uses_new_housing_endpoint(monkeypatch):
    calls = []

    def fake_resource_exists(url):
        calls.append(url)
        return True

    monkeypatch.setattr(reservation_service, "_resource_exists", fake_resource_exists)

    result = reservation_service.validate_cross_service_references(tenant_id=4, housing_id=8)

    assert result is None
    assert calls[0].endswith("/users/4")
    assert calls[1].endswith("/housing/8")


def test_is_housing_available_uses_available_field(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "_fetch_resource",
        lambda url: {"id": 1, "available": False},
    )

    result = reservation_service.is_housing_available(1)

    assert result is False


def test_create_reservation_request_returns_validation_error_before_db(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "validate_cross_service_references",
        lambda tenant_id, housing_id: {"error": "tenant_not_found"},
    )

    result = reservation_service.create_reservation_request(
        tenant_id=123,
        housing_id=10,
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    assert result == {"error": "tenant_not_found"}


def test_create_reservation_request_returns_error_for_invalid_date_range(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "validate_reservation_dates",
        lambda start_date, end_date: {"error": "invalid_date_range"},
    )

    result = reservation_service.create_reservation_request(
        tenant_id=1,
        housing_id=10,
        start_date="2026-06-01",
        end_date="2026-05-01",
    )

    assert result == {"error": "invalid_date_range"}


def test_create_reservation_request_returns_error_when_housing_is_not_available(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "validate_reservation_dates",
        lambda start_date, end_date: {
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
    )
    monkeypatch.setattr(reservation_service, "validate_cross_service_references", lambda tenant_id, housing_id: None)
    monkeypatch.setattr(reservation_service, "is_housing_available", lambda housing_id: False)

    result = reservation_service.create_reservation_request(
        tenant_id=1,
        housing_id=10,
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    assert result == {"error": "housing_not_available"}


def test_create_reservation_request_returns_error_when_period_overlaps(monkeypatch):
    monkeypatch.setattr(
        reservation_service,
        "validate_reservation_dates",
        lambda start_date, end_date: {
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
    )
    monkeypatch.setattr(reservation_service, "validate_cross_service_references", lambda tenant_id, housing_id: None)
    monkeypatch.setattr(reservation_service, "is_housing_available", lambda housing_id: True)
    monkeypatch.setattr(
        reservation_service,
        "has_overlapping_reservation",
        lambda housing_id, start_date, end_date: True,
    )

    result = reservation_service.create_reservation_request(
        tenant_id=1,
        housing_id=10,
        start_date="2026-05-01",
        end_date="2026-05-31",
    )

    assert result == {"error": "overlapping_reservation"}