from yota.nodes import *
import yota
from yota.validators import *

from weekly.models import Major, Team

class RegisterForm(yota.Form):
    username = EntryNode(validators=MinMaxValidator(3, 64))
    full_name = EntryNode(validators=MinMaxValidator(3, 64))
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
    username = EntryNode(css_class="form-control")
    password = PasswordNode(css_class="form-control")
    submit = SubmitNode(title="Login", css_class="btn-sm btn btn-primary")
