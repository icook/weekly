from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required

from weekly import app, db, lm
from weekly.forms import LoginForm, RegisterForm, PostForm, ImportForm, SettingsForm, CommentForm
from weekly.models import User, Post, Team, Major
from weekly.lib import week_human, get_now, week_through, send_email, catch_error_graceful

import mongoengine
import datetime
import time
import logging

@lm.user_loader
def load_user(id):
    return User.objects.get(id=id)

@app.before_request
def before_request():
    g.user = current_user

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           errmsg='The requested resource could not be found',
                           errno=404)

@app.errorhandler(403)
def page_not_found(e):
    return render_template('error.html',
                           errmsg='Access to the requested resource is denied',
                           errno=403)

@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html',
                           errmsg=('An internal application error has occured. '
                                   'Sorry about that, I\'ve likely made a '
                                   'mistake somewhere'),
                           errno=500)

@app.route('/announcements')
@app.route('/announcement/<id>')
@login_required
def announcements(id=None):
    if id is not None:
        announcements = [Post.objects.get(id=id), ]
    else:
        announcements = Post.objects.all().filter(announcement=True).order_by('-timestamp')
    return render_template('announce.html',
                           posts=announcements)

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
    try:
        post = Post.objects.get(id=postid)
    except Post.DoesNotExist:
        abort(404)

    if post.year < 0:
        subtitle = ''
    else:
        # Super sloppy un-abstracted pretty print for the current week
        sun = time.strptime('{0} {1} 1'.format(post.year, post.week), '%Y %W %w')
        sunday = time.strftime("%a, %d %b %Y", sun)
        sat = time.strptime('{0} {1} 5'.format(post.year, post.week), '%Y %W %w')
        saturday = time.strftime("%a, %d %b %Y", sat)
        subtitle = "{0} through {1}".format(sunday, saturday)

    form = CommentForm()

    # detects old editor request
    if request.args.get('oldeditor', 'false') == 'true':
        form.body.template = 'textarea_lnk'

    # Inject defaults if we're editing
    if comm_no:
        comment = post.comments[comm_no]
        form.body.data = comment.body
        form.submit.title = "Save"
    else:
        form.body.storage = "new_comment"

    # process a submission of the form
    if request.method == "POST":
        success = form.validate(request.form)
        data = form.data_by_attr()

        if success:
            try:
                if comm_no:
                    post.comments[comm_no].body = data['body']
                    post.save()
                else:
                    comment = post.add_comment(g.user.id, data['body'])
            except Exception:
                catch_error_graceful(form)
            else:
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
                form.start.add_msg(
                    {'message': 'Updated your name', 'type': 'success'})
            if int(form.type.data) != usr._type:
                usr._type = int(data['type'])
                form.start.add_msg(
                    {'message': 'Updated your account type', 'type': 'success'})
            if len(form.password.data) > 0:
                usr.password = data['password']
                form.start.add_msg(
                    {'message': 'Updated your password', 'type': 'success'})
            if form.email.data != usr.email:
                usr.email = data['email']
                form.start.add_msg(
                    {'message': 'Updated your email address', 'type': 'success'})
            if form.team.data != str(usr.team.id):
                usr.team = Team(id=data['team'])
                form.start.add_msg(
                    {'message': 'Updated your team', 'type': 'success'})
            if form.major.data != usr.major.key:
                usr.major = Major(id=data['major'])
                form.start.add_msg(
                    {'message': 'Updated your major', 'type': 'success'})

            for node in form._node_list:
                node.data = ''

            try:
                usr.save()
            except Exception:
                catch_error_graceful(form)


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
    usrs = User.objects.all().filter(active=True)
    return render_template('users.html', users=usrs)

@app.route('/post', methods = ['GET', 'POST'])
@app.route('/edit/<postid>', defaults={'announce': False}, methods = ['GET', 'POST'])
@app.route('/announce', defaults={'announce': True, 'postid': None}, methods = ['GET', 'POST'])
@login_required
def post(postid=None, announce=False):
    """ Create a new post (weekly post) or edit an existing one """
    if announce and not g.user.admin:
        abort(403)
    form = PostForm.get_form(announce)

    # detects old editor request
    if request.args.get('oldeditor', 'false') == 'true':
        form.body.template = 'textarea_lnk'

    # Inject defaults if we're editing
    if postid:
        # 404 the user if they're trying to edit something that doesn't exist
        try:
            post = Post.objects.get(id=postid)
        except (Post.DoesNotExist, mongoengine.errors.ValidationError):
            abort(404)
        form.body.data = post.body
        form.submit.title = "Save"
        # Sloppy way to remove the week selection
        form._node_list.remove(form.week)
        form.start.title = "Edit your weekly"
    else:
        form.body.storage = "new_post"

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
                    # if they're an admin and making announcement, null out
                    # the year and week, and set announcement flag
                    if g.user.admin and announce:
                        year = -1
                        week = -1
                        announce = True
                    else:
                        year, week = data['week'].split('-')
                        announce = False
                    post = Post(user=g.user.id,
                                year=year,
                                week=week,
                                announcement=announce,
                                body=data['body'])
                    post.save()
            except Exception:
                catch_error_graceful(form)
            else:
                return redirect(post.get_abs_url())

    return render_template('post.html',
                           form=form.render())

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
                            iform.start.add_msg(
                                {'message': 'Inserted user ' + user.username, 'type': 'success'})
                        except mongoengine.errors.NotUniqueError:
                            iform.start.add_msg(
                                {'message': 'User ' + user.username + ' already exists, and thus was not created'})
                        except Exception:
                            catch_error_graceful(form)


    # Handle logic of approving or denying user accounts
    if username is not None:
        if action == "approve":
            user = User.objects.get(username=username)
            if user.active:
                flash(user.username + " has already been activated",
                      category="danger")
                return redirect(url_for('admin'))
            user.active = True
            user.save()
            flash(user.username + " has been activated", category="success")
        elif action == "reject":
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return redirect(url_for('admin'))
            user.delete()
            flash(user.username + " has been removed", category="danger")
        elif action == "test_email":
            user = User.objects.get(username=username)
            if send_email(user, "mail/test.html"):
                flash(user.email + " has been sent a test email", category="success")
            else:
                flash("There was an error sending test email", category="danger")
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
                user = User.objects.get(username=data['username'].lower(), active=True)
            except User.DoesNotExist:
                form.start.add_msg({"message": "Invalid credentials, or account not active."})
            except Exception:
                catch_error_graceful(form)
            else:
                if user and user.check_password(data['password']):
                    login_user(user)
                    return redirect(url_for('index'))
                else:
                    form.start.add_msg({"message": "Invalid credentials, or account not active."})
    return render_template('login.html', form=form.render())

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


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
            except Exception:
                catch_error_graceful(form)
            else:
                form.start.add_msg(
                    {'message': 'You\'ve been successfully registered, your account is pending approval', 'type': 'success'})

    return render_template('signup.html', form=form.render())
