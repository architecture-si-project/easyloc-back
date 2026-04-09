from app import db


class Logement(db.Model):
    __tablename__ = "Logements"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    type = db.Column(db.String(50), nullable=False)
    localisation = db.Column(db.String(200), nullable=False)
    prix_par_nuit = db.Column(db.Float, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    proprietaire_id = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "titre": self.titre,
            "description": self.description,
            "type": self.type,
            "localisation": self.localisation,
            "prix_par_nuit": self.prix_par_nuit,
            "disponible": self.disponible,
            "proprietaire_id": self.proprietaire_id,
        }
