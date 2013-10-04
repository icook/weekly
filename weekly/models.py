from weekly import db

import cryptacular.bcrypt
import datetime
import mongoengine

from flask import url_for

from misaka import Markdown, HtmlRenderer

rndr = HtmlRenderer()
md = Markdown(rndr)

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()

class User(db.Document):
    _password = db.StringField(max_length=1023, required=True)
    username = db.StringField(max_length=32, min_length=3, unique=True)
    name = db.StringField(max_length=32, min_length=3, unique=True)
    team = db.ReferenceField('Team')
    major = db.ReferenceField('Major')
    email = db.StringField(required=True)
    admin = db.BooleanField(default=False)
    active = db.BooleanField(default=False)
    _type = db.IntField(min_value=0, max_value=3)

    @property
    def type(self):
        if self._type == 0:
            return 'Volunteer'
        elif self._type == 1:
            return 'Senior'
        else:
            return 'Alumni'

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, val):
        self._password = unicode(crypt.encode(val))

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

class Comment(db.EmbeddedDocument):
    body = db.StringField(min_length=10)
    user = db.ReferenceField(User, required=True)
    time = db.DateTimeField()

    @property
    def md_body(self):
        return md.render(self.body)

class Post(db.Document):
    id = db.ObjectIdField()
    body = db.StringField(min_length=10)
    timestamp = db.DateTimeField(default=datetime.datetime.now())
    year = db.IntField(required=True)
    week = db.IntField(required=True)
    user = db.ReferenceField(User, required=True)
    comments = db.ListField(db.EmbeddedDocumentField(Comment))

    @property
    def md_body(self):
        return md.render(self.body)

    @classmethod
    def next_week(self, week=None, year=None):
        now = datetime.datetime.now().isocalendar()
        if not week:
            week = now[1] - 1
        if not year:
            year = now[0]

        if week == 52:
            year += 1
            week = 0
        else:
            week += 1

        return url_for('index', week=week, year=year)

    @classmethod
    def prev_week(self, week=None, year=None):
        now = datetime.datetime.now().isocalendar()
        if not week:
            week = now[1] - 1
        if not year:
            year = now[0]

        if week == 0:
            year -= 1
            week = 52
        else:
            week -= 1

        return url_for('index', week=week, year=year)

    def add_comment(self, user, body):
        comment = Comment(user=user,
                          body=body,
                          time=datetime.datetime.now())
        self.comments.append(comment)
        self.save()


class Team(db.Document):
    id = db.ObjectIdField()
    text = db.StringField()

    def __str__(self):
        return self.text

    def users(self):
        return User.objects(team=self, _type=1)

class Major(db.Document):
    key = db.StringField(max_length=5, primary_key=True)
    text = db.StringField()

    def __str__(self):
        return self.text
