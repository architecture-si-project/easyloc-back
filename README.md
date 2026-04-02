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

## Lancer le projet avec Docker

Construire l’image Docker :

```bash
docker build -t easyloc-back .
```

Lancer le conteneur :

```bash
docker run -p 5000:5000 easyloc-back
```

L’API sera accessible à l’adresse suivante :

```text
http://localhost:5000
```