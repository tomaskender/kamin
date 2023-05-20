from mongoengine import *

class Property(Document):
    id = IntField(required=True, unique=True, primary_key=True)
    street = StringField(required=True)
    property_type = StringField(required=True)
    rooms = IntField(required=True)
    has_separate_kitchen = BooleanField(required=True)
    house_size = IntField(required=True)
    latitude = FloatField(required=True)
    longitude = FloatField(required=True)
    price = IntField(required=True)

class Town(Document):
    town = StringField(required=True, unique=True, primary_key=True)
    added = DateField(required=True)
    tracked = BooleanField(required=True, default=True)
    properties = ListField(EmbeddedDocumentField(Property))
