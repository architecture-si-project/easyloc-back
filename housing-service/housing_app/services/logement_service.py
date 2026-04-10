from housing_app import db
from housing_app.models.logement import Logement


def get_all():
    return Logement.query.all()


def get_by_id(logement_id):
    return Logement.query.get(logement_id)


def search(localisation=None, type_=None, prix_max=None):
    query = Logement.query
    if localisation:
        query = query.filter(Logement.localisation.ilike(f"%{localisation}%"))
    if type_:
        query = query.filter(Logement.type == type_)
    if prix_max is not None:
        query = query.filter(Logement.prix_par_nuit <= prix_max)
    return query.all()


def create(data):
    logement = Logement(
        titre=data["titre"],
        description=data.get("description", ""),
        type=data["type"],
        localisation=data["localisation"],
        prix_par_nuit=data["prix_par_nuit"],
        disponible=data.get("disponible", True),
        proprietaire_id=data["proprietaire_id"],
    )
    db.session.add(logement)
    db.session.commit()
    return logement


def update(logement, data):
    for field in ["titre", "description", "type", "localisation", "prix_par_nuit", "disponible"]:
        if field in data:
            setattr(logement, field, data[field])
    db.session.commit()
    return logement


def delete(logement):
    db.session.delete(logement)
    db.session.commit()
