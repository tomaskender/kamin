from mongoengine import *

class Property(EmbeddedDocument):
    _id = IntField(required=True, index=True)
    street = StringField(required=True)
    name = StringField(required=True)
    rooms = IntField(required=True)
    has_separate_kitchen = BooleanField(required=True)
    size = IntField(required=True)
    latitude = FloatField(required=True)
    longitude = FloatField(required=True)
    price = IntField(required=True)
    checked = DateField(required=True, index=True)

class Town(Document):
    _id = StringField(required=True, primary_key=True)
    added = DateField(required=True)
    last_update = DateField(required=True)
    tracked = BooleanField(required=True, default=True)
    properties = EmbeddedDocumentListField(Property)
