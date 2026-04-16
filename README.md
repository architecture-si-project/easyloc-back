# easyloc-back

Ce projet correspond au backend de l’application EasyLoc, développé avec Flask.

## Lancer le projet avec Docker Compose

Construire et lancer les services (backend + base de données) :

```bash
docker compose up --build
```

L’API sera accessible à l’adresse suivante :

User service :
```text
http://localhost:5001
```

Housing service :
```text
http://localhost:5002
```

Reservation service :
```text
http://localhost:5003
```

## Swagger (single URL)

All services are documented in one Swagger UI:

```text
http://localhost:5000/docs
```

If needed, raw OpenAPI sources are still available per service:

```text
http://localhost:5001/openapi.json
http://localhost:5002/openapi.json
http://localhost:5003/openapi.json
```

---

## Réinitialiser la base de données

Le script SQL d’initialisation est exécuté uniquement au premier lancement.

Pour réinitialiser complètement la base :

```bash
docker compose down -v
docker compose up --build
```