CREATE TABLE IF NOT EXISTS housing (
    id                SERIAL PRIMARY KEY,
    title             VARCHAR(200) NOT NULL,
    description       TEXT DEFAULT '',
    property_type     VARCHAR(50) NOT NULL,
    location          VARCHAR(200) NOT NULL,
    price_per_night   FLOAT NOT NULL,
    available         BOOLEAN DEFAULT TRUE,
    owner_id          INTEGER NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
