# easyloc-back

Ce projet correspond au backend de l’application EasyLoc, développé avec Flask.

## Lancer le projet avec Python

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Lancer l’application :

```bash
python app.py
```

L’API sera accessible à l’adresse suivante :

```text
http://localhost:5000
```

---

## Lancer le projet avec Docker Compose

Construire et lancer les services (backend + base de données) :

```bash
docker compose up --build
```

L’API sera accessible à l’adresse suivante :

```text
http://localhost:5000
```

---

## Réinitialiser la base de données

Le script SQL d’initialisation est exécuté uniquement au premier lancement.

Pour réinitialiser complètement la base :

```bash
docker compose down -v
docker compose up --build
```