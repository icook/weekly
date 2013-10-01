from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required

import mongoengine
import datetime
import time

from weekly import app, db, lm
from weekly.forms import LoginForm, RegisterForm, PostForm, ImportForm, SettingsForm
from weekly.models import User, Post, Team, Major

@lm.user_loader
def load_user(id):
    return User.objects.get(id=id)

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/<int:year>/<int:week>')
@login_required
def index(week=None, year=None):
    now = datetime.datetime.now().isocalendar()
    if not week:
        week = now[1] - 1
    if not year:
        year = now[0]

    sun = time.strptime('{0} {1} 1'.format(year, week), '%Y %W %w')
    sunday = time.strftime("%a, %d %b %Y", sun)
    sat = time.strptime('{0} {1} 5'.format(year, week), '%Y %W %w')
    saturday = time.strftime("%a, %d %b %Y", sat)
    subtitle = "{0} through {1}".format(sunday, saturday)

    posts = Post.objects(week=week, year=year)
    teams = {}
    for post in posts:
        tid = post.user.team.id
        if tid in teams:
            teams[tid].append(post)
        else:
            teams[tid] = [post]


    return render_template('index.html',
                           week=week,
                           year=year,
                           subtitle=subtitle)

@app.route('/settings', methods = ['GET', 'POST'])
@login_required
def settings():
    usr = g.user
    form = SettingsForm()
    # set the form defaults to user info
    form.full_name.data = usr.name
    form.alumni.data = usr.alumni
    form.email.data = usr.email
    if request.method == "POST":
        success, invalid_nodes = form.validate(request.form)
        data = form.data_by_attr()

        # the lazist logic block, but it'll work for now
        if success:
            if form.full_name.data != usr.name:
                usr.name = data['full_name']
            if form.alumni.data != usr.alumni:
                usr.alumni = data['alumni']
            if len(form.password) > 0:
                usr.password = data['password']


    return render_template('settings.html', form=form.render())

@app.route('/users')
@login_required
def users():
    usrs = User.objects.all()
    return render_template('users.html', users=usrs)

@app.route('/post', methods = ['GET', 'POST'])
@login_required
def post():
    form = PostForm.get_form()
    if request.method == "POST":
        success, invalid_nodes = form.validate(request.form)
        data = form.data_by_attr()
        if success:
            try:
                year, week = data['week'].split('-')
                post = Post(user=g.user.id,
                            year=year,
                            week=week,
                            body=data['body'])
                post.save()
            except mongoengine.errors.OperationError:
                form.start.add_error({'message': 'Unknown database error, please retry.'})
            except mongoengine.errors.ValidationError:
                form.start.add_error({'message': 'You\'ve already posted for this date'})
            else:
                return redirect(url_for('index', week=week, year=year) + "#" + str(post.id))

    return render_template('post.html', form=form.render())

@app.route('/admin', methods = ['GET', 'POST'])
@login_required
def admin():
    if not g.user.admin:
        return redirect(url_for('index'))

    iform = ImportForm()
    test_table = None
    if request.method == "POST":
        tp = request.form['_arg_form']
        if tp == "import":
            success, invalid_nodes = iform.validate(request.form)
            data = iform.data_by_attr()
            if success:
                if 'go' in data:
                    test_table = iform.body.valid_data

    return render_template('admin.html',
                           iform=iform.render(),
                           test_table=test_table)

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
                            name=data['full_name'],
                            alumni=(data['alumni'] == "true"),
                            username=data['username'])
                # In case there are no options, only set these if possible
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
