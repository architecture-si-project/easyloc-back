class Housing:
    def __init__(
        self,
        id,
        title,
        description,
        property_type,
        location,
        price_per_night,
        available,
        owner_id,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.property_type = property_type
        self.location = location
        self.price_per_night = price_per_night
        self.available = available
        self.owner_id = owner_id
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type,
            "location": self.location,
            "price_per_night": self.price_per_night,
            "available": self.available,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

