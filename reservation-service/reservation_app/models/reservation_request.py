class ReservationRequest:
    reservation_id: int
    tenant_id: int
    housing_id: int
    start_date: str
    end_date: str
    status: str
    notes: str | None
    created_at: str
    updated_at: str