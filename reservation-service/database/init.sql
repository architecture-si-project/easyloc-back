CREATE TABLE IF NOT EXISTS reservation_requests
(
    reservation_id SERIAL PRIMARY KEY,
    tenant_id      INTEGER      NOT NULL,
    housing_id     INTEGER      NOT NULL,
    start_date     DATE         NOT NULL,
    end_date       DATE         NOT NULL,
    status         VARCHAR(30)  NOT NULL DEFAULT 'pending',
    notes          TEXT,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT reservation_dates_check CHECK (start_date <= end_date)
);

CREATE TABLE IF NOT EXISTS reservation_process_events
(
    event_id        SERIAL PRIMARY KEY,
    reservation_id  INTEGER      NOT NULL REFERENCES reservation_requests (reservation_id) ON DELETE CASCADE,
    old_status      VARCHAR(30),
    new_status      VARCHAR(30)  NOT NULL,
    actor_id        INTEGER,
    comment         TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reservation_requests_tenant ON reservation_requests (tenant_id);
CREATE INDEX IF NOT EXISTS idx_reservation_requests_housing ON reservation_requests (housing_id);
CREATE INDEX IF NOT EXISTS idx_reservation_requests_status ON reservation_requests (status);
CREATE INDEX IF NOT EXISTS idx_reservation_events_reservation ON reservation_process_events (reservation_id);
