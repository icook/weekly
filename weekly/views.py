from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required

import mongoengine
import datetime
import time
import logging

from weekly import app, db, lm
from weekly.forms import LoginForm, RegisterForm, PostForm, ImportForm, SettingsForm, CommentForm
from weekly.models import User, Post, Team, Major
from weekly.lib import week_human, get_now, week_through

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
    now = get_now().isocalendar()
    if not week:
        week = now[1] - 2
    if not year:
        year = now[0]

    subtitle = "{0} through {1}".format(*week_through(year, week))

    # Group all the users into teams for display
    teams = {}
    for team in Team.objects.all():
        if team.text == "Other":
            continue

        posts = []
        for user in team.users():
            try:
                posts.append((True, Post.objects.get(user=user, week=week, year=year)))
            except Post.DoesNotExist:
                posts.append((False, user))

        teams[team.text] = posts


    return render_template('index.html',
                           week=week,
                           year=year,
                           subtitle=subtitle,
                           teams=teams,
                           human=week_human(week),
                           Post=Post)


@app.route('/comment/<postid>', methods = ['GET', 'POST'])
@app.route('/comment/edit/<postid>/<int:comm_no>', methods = ['GET', 'POST'])
@login_required
def comment(postid=None, comm_no=None):
    post = Post.objects.get(id=postid)

    # Super sloppy un-abstracted pretty print for the current week
    sun = time.strptime('{0} {1} 1'.format(post.year, post.week), '%Y %W %w')
    sunday = time.strftime("%a, %d %b %Y", sun)
    sat = time.strptime('{0} {1} 5'.format(post.year, post.week), '%Y %W %w')
    saturday = time.strftime("%a, %d %b %Y", sat)
    subtitle = "{0} through {1}".format(sunday, saturday)

    form = CommentForm()

    # Inject defaults if we're editing
    if comm_no:
        comment = post.comments[comm_no]
        form.body.data = comment.body
        form.submit.title = "Save"

    # process a submission of the form
    if request.method == "POST":
        success = form.validate(request.form)
        data = form.data_by_attr()

        if success:
            if comm_no:
                post.comments[comm_no].body = data['body']
                post.save()
            else:
                comment = post.add_comment(g.user.id, data['body'])

            return redirect(post.get_abs_url_comm(comment))

    return render_template('comment.html',
                           form=form.render(),
                           post=post,
                           subtitle=subtitle)

@app.route('/settings', methods = ['GET', 'POST'])
@login_required
def settings():
    usr = g.user
    form = SettingsForm.get_form()
    if request.method == "POST":
        success = form.validate(request.form)
        data = form.data_by_attr()

        # the lazist logic block, but it'll work for now
        if success:
            if form.full_name.data != usr.name:
                usr.name = data['full_name']
                form.start.add_error(
                    {'message': 'Updated your name', 'type': 'success'})
            if int(form.type.data) != usr._type:
                usr._type = int(data['type'])
                form.start.add_error(
                    {'message': 'Updated your account type', 'type': 'success'})
            if len(form.password.data) > 0:
                usr.password = data['password']
                form.start.add_error(
                    {'message': 'Updated your password', 'type': 'success'})
            if form.email.data != usr.email:
                usr.email = data['email']
                form.start.add_error(
                    {'message': 'Updated your email address', 'type': 'success'})
            if form.team.data != str(usr.team.id):
                usr.team = Team(id=data['team'])
                form.start.add_error(
                    {'message': 'Updated your team', 'type': 'success'})
            if form.major.data != usr.major.key:
                usr.major = Major(id=data['major'])
                form.start.add_error(
                    {'message': 'Updated your major', 'type': 'success'})

            for node in form._node_list:
                node.data = ''

            try:
                usr.save()
            except mongoengine.errors.OperationError:
                form.start.add_error({'message': 'Unknown database error, please retry.'})
                logging.warn("Post data contents: {0}\n"
                             "Form data contents: {1}".format(data, request.form))
            except mongoengine.errors.ValidationError:
                form.start.add_error({'message': 'Validation error. This shouldn\t happen :('})
                logging.warn("Post data contents: {0}\n"
                             "Form data contents: {1}".format(data, request.form))
            except mongoengine.errors.NotUniqueError:
                form.start.add_error({'message': 'Not unique error. This shouldn\'t happen.'})
                logging.warn("Post data contents: {0}\n"
                             "Form data contents: {1}".format(data, request.form))


    # set the form defaults to user info
    form.full_name.data = usr.name
    form.type.data = usr._type
    form.email.data = usr.email
    form.team.data = usr.team.id
    form.major.data = usr.major.id

    return render_template('settings.html', form=form.render())

@app.route('/users')
@login_required
def users():
    usrs = User.objects.all()
    return render_template('users.html', users=usrs)

@app.route('/post', methods = ['GET', 'POST'])
@app.route('/edit/<postid>', methods = ['GET', 'POST'])
@login_required
def post(postid=None):
    """ Create a new post (weekly post) or edit an existing one """
    form = PostForm.get_form()

    # Inject defaults if we're editing
    if postid:
        post = Post.objects.get(id=postid)
        form.body.data = post.body
        form.submit.title = "Save"
        # Sloppy way to remove the week selection
        form._node_list.remove(form.week)
        edit = True
    else:
        edit = False

    if request.method == "POST":
        success = form.validate(request.form)
        data = form.data_by_attr()
        if success:
            try:
                if postid:
                    # update the post
                    post.body = form.body.data
                    post.save()
                else:
                    # create a new post
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
                return redirect(post.get_abs_url())

    return render_template('post.html',
                           form=form.render(),
                           edit=edit)

@app.route('/admin', methods = ['GET', 'POST'])
@app.route('/admin/<action>/<username>', methods = ['GET', 'POST'])
@login_required
def admin(username=None, action=None):
    if not g.user.admin:
        return redirect(url_for('index'))

    msg = ""

    # Make a little list of major keys for reference
    majors = []
    for major in Major.objects.all():
        majors.append(major.key)
    majors = ', '.join(majors)

    # Handle the logic of doing mass imports
    iform = ImportForm()
    test_table = None
    if request.method == "POST":
        tp = request.form['_arg_form']
        if tp == "import":
            success = iform.validate(request.form)
            data = iform.data_by_attr()
            if success:
                if not data['go']:
                    test_table = iform.body.valid_data
                else:
                    for user in iform.body.valid_data:
                        try:
                            team = Team.objects.get_or_create(text=user.team_txt)
                            delattr(user, 'team_txt')
                            user.team = team[0]
                            user.password = user.username
                            user.active = True
                            user.save()
                            iform.start.add_error(
                                {'message': 'Inserted user ' + user.username, 'type': 'success'})
                        except mongoengine.errors.NotUniqueError:
                            iform.start.add_error(
                                {'message': 'User ' + user.username + ' already exists'})


    # Handle logic of approving or denying user accounts
    if username is not None:
        if action == "approve":
            user = User.objects.get(username=username)
            user.active = True
            user.save()
            msg = user.username + " has been activated"
    users = User.objects(active=False).all()

    return render_template('admin.html',
                           iform=iform.render(),
                           test_table=test_table,
                           majors=majors,
                           users=users,
                           msg=msg,
                           msg_type="success")

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    form = LoginForm()
    if request.method == "POST":
        success = form.validate(request.form)
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
        success = form.validate(request.form)
        data = form.data_by_attr()
        if success:
            try:
                user = User(email=data['email'],
                            name=data['full_name'],
                            _type=data['type'],
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
