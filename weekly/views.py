from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required

import mongoengine

from weekly import app, db, lm
from weekly.forms import LoginForm, RegisterForm
from weekly.models import User, Post, Team, Major

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()
    if request.method == "POST":
        success, invalid_nodes = form.validate(request.form)
        data = form.data_by_attr()
        if success:
            try:
                user = User.objects.get(username=data['username'])
            except User.DoesNotExist:
                pass
            else:
                if user and user.check_password(data['password']):
                    login_user(user)
                    return redirect(url_for('index'))
                else:
                    form.start.add_error({"message": "Invalid credentials"})
    return render_template('login.html', form=form.render())

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = RegisterForm.get_form()
    if request.method == 'POST':
        success, invalid_nodes = form.validate(request.form)
        data = form.data_by_attr()
        if success:
            try:
                user = User(emails=data['email'],
                            username=data['username'])
                # In case there are no options, only set these if possible
                print data
                if data['team']:
                    user.team = Team(id=data['team'])
                if data['major']:
                    user.major = Major(key=data['major'])
                user.password = data['password']
                user.save()
            except (mongoengine.errors.OperationError, mongoengine.errors.ValidationError):
                raise
                form.start.add_error(
                    {'message': 'Unknown database error, please retry.'})
            else:
                form.start.add_error(
                    {'message': 'You\'ve been successfully registered, your account is pending approval', 'type': 'success'})
    return render_template('signup.html', form=form.render())
