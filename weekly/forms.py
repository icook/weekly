from yota import Check, Form, Listener, Blueprint
import yota.validators as validators
import yota.nodes as nodes
from yota.exceptions import *

import time
import datetime

from weekly.models import Major, Team, User, Post
from weekly.lib import week_human, get_now, week_through

from flask import g

Form.form_class = "form-horizontal"

class CheckNode(nodes.Base):
    """ Creates a simple checkbox for your form. """
    template = 'checkbox'

    def resolve_data(self, data):
        if self.name in data:
            self.data = True
        else:
            # Unchecked checkboxes don't submit any data so we'll set the
            # value to false if there is no post data
            self.data = False


class SettingsForm(Form):
    full_name = nodes.Entry(title="Display title", validators=validators.MinMax(3, 64))
    type = nodes.List(items=[(0, 'Volunteer'),
                           (1, 'Senior'),
                           (2, 'Alumni'),
                           (3, 'Other')])
    password = nodes.Password()
    password_confirm = nodes.Password(title="Confirm")
    _valid_pass = Check(validators.Matching(message="Password fields must match"),
                        "password",
                        "password_confirm")
    email = nodes.Entry(validators=validators.Email())
    submit = nodes.Submit(title="Update")

    @classmethod
    def get_form(cls):
        form = cls()
        lst = []
        for major in Major.objects.all():
            lst.append((major.key, major.text))
        form.insert_node_after('full_name', nodes.List(_attr_name='major',
                                                items=lst))
        lst = []
        for team in Team.objects.all():
            lst.append((team.id, team.text))
        form.insert_node_after('full_name', nodes.List(_attr_name='team',
                                                items=lst))
        return form


    def validator(self):
        if len(self.password.data) > 0:
            if len(self.password.data) > 128:
                self.password.add_msg({'message': 'Password cannot be longer than 32 characters'})
            elif len(self.password.data) < 5:
                self.password.add_msg({'message': 'Password cannot be fewer than 5 characters'})
            elif ' ' in self.password.data:
                self.password.add_msg({'message': 'Password must not contain spaces'})



class RegisterForm(Form):
    username = nodes.Entry(validators=validators.MinMax(3, 32))
    full_name = nodes.Entry(title="Display Name", validators=validators.MinMax(3, 128))
    type = nodes.List(items=[(0, 'Volunteer'),
                           (1, 'Senior'),
                           (2, 'Alumni'),
                           (3, 'Other')])
    password = nodes.Password(validators=validators.MinMax(5, 64))
    password_confirm = nodes.Password(title="Confirm")
    _valid_pass = Check(validators.Matching(message="Password fields must match"),
                        "password",
                        "password_confirm")
    email = nodes.Entry(validators=validators.Email())
    submit = nodes.Submit(title="Sign Up", css_class="btn-sm btn btn-success")

    def validator(self):
        # Check for a unique username
        try:
            user = User.objects.get(username=self.username.data)
        except User.DoesNotExist:
            pass
        else:
            # Give em a bit of help if they possibly just tried to register twice
            if user.active:
                self.username.add_msg(message='Username is taken. That account is currently active.')
            else:
                self.username.add_msg(message='Username is taken. That account is currently pending activation.')

        # And a unique email address
        try:
            user = User.objects.get(email=self.email.data)
        except User.DoesNotExist:
            pass
        else:
            # Give em a bit of help if they possibly just tried to register twice
            if user.active:
                self.username.add_msg(message='Email address is already in use. That account is currently active.')
            else:
                self.username.add_msg(message='Email address is already in use. That account is currently pending activation.')


        if ' ' in self.password:
            self.password.add_msg({'message': 'Password must not contain spaces'})

        if ' ' in self.username:
            self.password.add_msg({'message': 'Username cannot contain spaces'})

    @classmethod
    def get_form(cls):
        form = cls()
        lst = []
        for major in Major.objects.all():
            lst.append((major.key, major.text))
        form.insert_node_after('full_name', nodes.List(_attr_name='major',
                                                items=lst))
        lst = []
        for team in Team.objects.all():
            lst.append((team.id, team.text))
        form.insert_node_after('full_name', nodes.List(_attr_name='team',
                                                items=lst))
        return form


class CommentForm(Form):
    body = nodes.Textarea(rows=25,
                        columns=100,
                        css_class="form-control",
                        template='epictext',
                        validators=validators.MinLength(10))
    submit = nodes.Submit(title="Add Comment")


class LoginForm(Form):
    username = nodes.Entry()
    password = nodes.Password()
    submit = nodes.Submit(title="Login")

class ImportForm(Form):
    hidden = {'form': 'import'}
    go = CheckNode(title="Actually Insert?")
    body = nodes.Textarea(rows=25,
                        columns=100,
                        css_class="form-control",
                        validators=validators.MinLength(10))
    submit = nodes.Submit(title="Import")

    def validator(self):
        majlst = []
        for maj in Major.objects.all():
            majlst.append(maj.key)

        users = []
        for ln in str(self.body.data).splitlines(True):
            user = User()
            # clean up and strip the list
            pts = [x.strip() for x in ln.split(',')]
            # lowercase specific parts
            pts[2] = pts[2].lower()
            pts[4] = pts[4].lower()
            pts[5] = pts[5].lower().capitalize()

            if pts[2] not in ["alum", "senior", "vol", "other"]:
                self.body.add_msg({'message': pts[1] + ' type is invalid.'})
            else:
                if pts[2] == "alum":
                    user._type = 2
                elif pts[2] == "senior":
                    user._type = 1
                elif pts[2] == "vol":
                    user._type = 0
                else:
                    user._type = 3

            if pts[4].lower() not in majlst:
                self.body.add_msg({'message': pts[1] + ' major is invalid.'})
            else:
                user.major = Major.objects.get(key=pts[4])

            if not Email().valid(pts[3]):
                self.body.add_msg({'message': pts[1] + ' email is invalid.'})
            else:
                user.email = pts[3]

            try:
                Team.objects.get(text=pts[5])
            except Team.DoesNotExist:
                self.start.add_msg(
                    {'message': pts[1] + '\'s team ' + pts[5] + ' does not exist!',
                     'type': 'warn',
                     'block': False})
            user.team_txt = pts[5]

            user.name = pts[1]
            user.username = pts[0]

            users.append(user)

        setattr(self.body, 'valid_data', users)



class PostForm(Form):
    title = "Post A New Weekly"
    body = nodes.Textarea(rows=25,
                        columns=100,
                        css_class="form-control",
                        validators=validators.MinLength(10),
                        template='epictext')
    submit = nodes.Submit(title="Post")

    @classmethod
    def get_form(cls, announce):
        form = cls()
        form.announcement = announce
        if not announce:
            now = get_now().isocalendar()
            weeks = []
            data = None
            for i in range(-3, 3):
                sun, sat = week_through(now[0], now[1]+i)
                tag = "{0}-{1}".format(now[0], now[1]+i)
                if i == -1:
                    data = tag
                weeks.append(
                    (tag, "{0} ({1} through {2})".format(week_human(now[1]+i), sun, sat))
                )

            form.insert_node(1, nodes.List(_attr_name='week', items=weeks, data=data))
        else:
            form.start.title = "Post a new announcement"


        return form

    def validator(self):
        if self.announcement == False:
            try:
                year, week = self.week.data.split('-')
                pst = Post.objects.get(year=year, user=g.user.id, week=week)
            except Post.DoesNotExist:
                pass
            else:
                self.week.add_msg({'message': 'A post for the time already exists. You can edit that post <a href="{0}">here</a>.'.format(pst.get_edit_url())})
