from yota.nodes import *
from yota.validators import *
import yota
import time
import datetime

from weekly.models import Major, Team


class CheckNode(BaseNode):
    """ Creates a simple checkbox for your form. """
    template = 'checkbox'

    def resolve_data(self, data):
        if self.name in data:
            self.data = True
        else:
            # Unchecked checkboxes don't submit any data so we'll set the
            # value to false if there is no post data
            self.data = False


class SettingsForm(yota.Form):
    full_name = EntryNode(validators=MinMaxValidator(3, 64))
    alumni = CheckNode()
    password = PasswordNode()
    password_confirm = PasswordNode(title="Confirm")
    _valid_pass = Check(MatchingValidator(message="Password fields must match"),
                        "password",
                        "password_confirm")
    email = EntryNode(validators=EmailValidator())
    submit = SubmitNode(title="Update")

    @classmethod
    def get_form(cls):
        form = cls()
        lst = []
        for major in Major.objects.all():
            lst.append((major.key, major.text))
        form.insert_after('full_name', ListNode(_attr_name='major',
                                                items=lst))
        lst = []
        for team in Team.objects.all():
            lst.append((team.id, team.text))
        form.insert_after('full_name', ListNode(_attr_name='team',
                                                items=lst))
        return form


    def validator(self):
        self.alumni = self.alumni == "true"

        if len(self.password) > 0:
            if len(self.password) > 32:
                self.password.add_error({'message': 'Password cannot be longer than 32 characters'})
            elif len(self.password) < 5:
                self.password.add_error({'message': 'Password cannot be fewer than 5 characters'})
            elif ' ' in self.password:
                self.password.add_error({'message': 'Password must not contain spaces'})



class RegisterForm(yota.Form):
    username = EntryNode(validators=MinMaxValidator(3, 64))
    full_name = EntryNode(validators=MinMaxValidator(3, 64))
    alumni = CheckNode()
    password = PasswordNode(validators=MinMaxValidator(5, 64))
    password_confirm = PasswordNode(title="Confirm")
    _valid_pass = Check(MatchingValidator(message="Password fields must match"),
                        "password",
                        "password_confirm")
    email = EntryNode(validators=EmailValidator())
    submit = SubmitNode(title="Sign Up", css_class="btn-sm btn btn-success")

    def validator(self):
        if ' ' in self.password:
            self.password.add_error({'message': 'Password must not contain spaces'})

    @classmethod
    def get_form(cls):
        form = cls()
        lst = []
        for major in Major.objects.all():
            lst.append((major.key, major.text))
        form.insert_after('full_name', ListNode(_attr_name='major',
                                                items=lst))
        lst = []
        for team in Team.objects.all():
            lst.append((team.id, team.text))
        form.insert_after('full_name', ListNode(_attr_name='team',
                                                items=lst))
        return form

class LoginForm(yota.Form):
    username = EntryNode()
    password = PasswordNode()
    submit = SubmitNode(title="Login")

class ImportForm(yota.Form):
    hidden = {'form': 'import'}
    go = CheckNode(title="Actually Insert?")
    body = TextareaNode(rows=25,
                        columns=100,
                        css_class="form-control",
                        validators=MinLengthValidator(10))
    submit = SubmitNode(title="Import")

    def validator(self):
        majlst = []
        for maj in Major.objects.all():
            majlst.append(maj.key)

        users = []
        for ln in str(self.body.data).splitlines(True):
            user = {}
            # clean up and strip the list
            pts = [x.strip() for x in ln.split(',')]
            # lowercase specific parts
            pts[2] = pts[2].lower()
            pts[4] = pts[4].lower()
            pts[5] = pts[5].lower().capitalize()

            if pts[2] not in ["false", "true"]:
                self.body.add_error({'message': pts[1] + ' alumni status is invalid.'})
            else:
                user['alumni'] = bool(pts[2] == "true")

            if pts[4].lower() not in majlst:
                self.body.add_error({'message': pts[1] + ' major is invalid.'})
            else:
                user['major'] = Major.objects.get(key=pts[4])

            if not EmailValidator().valid(pts[3]):
                self.body.add_error({'message': pts[1] + ' email is invalid.'})
            else:
                user['email'] = pts[3]

            try:
                Team.objects.get(text=pts[5])
            except Team.DoesNotExist:
                self.start.add_error(
                    {'message': pts[1] + '\'s team ' + pts[5] + ' does not exist!',
                     'type': 'warn',
                     'block': False})
            user['team'] = pts[5]

            user['name'] = pts[1]
            user['username'] = pts[0]

            users.append(user)

        setattr(self.body, 'valid_data', users)



class PostForm(yota.Form):
    body = TextareaNode(rows=25,
                        columns=100,
                        css_class="form-control",
                        validators=MinLengthValidator(10))
    submit = SubmitNode(title="Post")

    @classmethod
    def get_form(cls):
        form = cls()
        now = datetime.datetime.now().isocalendar()
        weeks = []
        data = None
        for i in range(-3, 3):
            sun = time.strptime('{0} {1} 1'.format(now[0], now[1]+i), '%Y %W %w')
            sunday = time.strftime("%a, %d %b %Y", sun)
            sat = time.strptime('{0} {1} 5'.format(now[0], now[1]+i), '%Y %W %w')
            saturday = time.strftime("%a, %d %b %Y", sat)
            tag = "{0}-{1}".format(now[0], now[1]+i)
            if i == -1:
                data = tag
            weeks.append(
                (tag, "{0} through {1}".format(sunday, saturday))
            )

        form.insert(1, ListNode(_attr_name='week', items=weeks, data=data))
        return form

    def error_header_generate(self):
        self.start.add_error({'message': 'Please fix the errors below'})
