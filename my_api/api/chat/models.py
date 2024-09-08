from django.db import models
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import ReferenceField, StringField, DateTimeField, datetime, ListField, EmbeddedDocumentField
from mongoengine import CASCADE

# Create your models here.

class Message(EmbeddedDocument):
    sender = ReferenceField('CustomUserModel')
    message = StringField(required=True)
    # timestamp = DateTimeField(default=datetime.UTC)

class Room(Document):
    users_within = ListField(ReferenceField('CustomUserModel', required=True))
    messages = ListField(EmbeddedDocumentField(Message), default=[])

    meta = {
        'collection': 'chat_rooms'
    }

    def add_message(self, message):
        self.update(push__messages=message)

    def create_room(self, users):
        self.users_within = [*users]
        self.save()
        for user in users:
            user.add_room_to_user(self)