from weekly import db

import cryptacular.bcrypt
import datetime
import mongoengine

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()

class User(db.Document):
    id = db.ObjectIdField()
    _password = db.StringField(max_length=1023, required=True)
    username = db.StringField(max_length=32, min_length=3, unique=True)
    team = db.ReferenceField('Team')
    major = db.ReferenceField('Major')
    email = db.StringField()
    admin = db.BooleanField(default=False)
    active = db.BooleanField(default=False)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, val):
        print val
        self._password = unicode(crypt.encode(val))
        print self._password

    def check_password(self, password):
        return crypt.check(self._password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Post(db.Document):
    id = db.ObjectIdField()
    body = db.StringField()
    timestamp = db.DateTimeField()
    user = db.ReferenceField(User)

class Team(db.Document):
    id = db.ObjectIdField(primary_key=True)
    text = db.StringField()

    def __str__(self):
        return self.text

class Major(db.Document):
    key = db.StringField(max_length=5, primary_key=True)
    text = db.StringField()

    def __str__(self):
        return self.text
