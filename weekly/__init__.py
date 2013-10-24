from flask import Flask, g
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, current_user

from jinja2 import FileSystemLoader

from yota.renderers import JinjaRenderer
from yota import Form

from weekly import data

import babel.dates as dates
import os
import datetime

root = os.path.abspath(os.path.dirname(__file__) + '/../')

# initialize our flask application
app = Flask(__name__, static_folder='../static', static_url_path='/static')

# Setup login stuff
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

# set our template path
app.jinja_loader = FileSystemLoader(os.path.join(root, 'templates'))
# setup mongo connection information
if os.getenv('PRODUCTION', False):
    app.config.from_pyfile('../../settings.cfg')
else:
    app.config.from_pyfile('../settings.cfg')
db = MongoEngine(app)


# patch yota to use bootstrap3
JinjaRenderer.templ_type = 'bs3'
JinjaRenderer.search_path.insert(0, root + "/templates/yota/")
Form.type_class_map = {'error': 'alert alert-danger',
                      'info': 'alert alert-info',
                      'success': 'alert alert-success',
                      'warn': 'alert alert-warning'}

# General configuration
# ======================

# Add a date format filter to jinja templating
@app.template_filter('datetime')
def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    return dates.format_datetime(value, format)

@app.template_filter('date')
def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y"
    elif format == 'medium':
        format="EE dd.MM.y"
    return dates.format_datetime(value, format)

@app.template_filter('date_ago')
def format_date_ago(time):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime.datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

from weekly import views, models

# check to make sure our desired majors are in the database
for major, key in data.majors:
    models.Major.objects.get_or_create(key=key, text=major)
# check to make sure our desired majors are in the database
for team in data.teams:
    models.Team.objects.get_or_create(text=team)
