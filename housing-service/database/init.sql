CREATE TABLE IF NOT EXISTS "Logements" (
    id               SERIAL PRIMARY KEY,
    titre            VARCHAR(200) NOT NULL,
    description      TEXT DEFAULT '',
    type             VARCHAR(50) NOT NULL,
    localisation     VARCHAR(200) NOT NULL,
    prix_par_nuit    FLOAT NOT NULL,
    disponible       BOOLEAN DEFAULT TRUE,
    proprietaire_id  INTEGER NOT NULL
);
