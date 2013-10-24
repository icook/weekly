from flask import render_template, current_app, request
from . import app

import datetime
import time
import smtplib
import mongoengine
import sys


def get_now():
    return datetime.datetime.now() - datetime.timedelta(hours=4)


def week_through(year, week):
    sun = time.strptime('{0} {1} 1'.format(year, week), '%Y %W %w')
    sunday = time.strftime("%a, %d %b %Y", sun)
    sat = time.strptime('{0} {1} 0'.format(year, week), '%Y %W %w')
    saturday = time.strftime("%a, %d %b %Y", sat)
    return sunday, saturday


def week_human(week):
    now = get_now().isocalendar()
    diff = (now[1] - 1) - week
    if diff == -1:
        return "Next Week"
    elif diff == 1:
        return "Last Week"
    elif diff < 0:
        return "{0} weeks in the future".format(diff*-1)
    elif diff > 0:
        return "{0} weeks ago".format(diff)
    else:
        return "This Week"


def send_email(user, template, **kwargs):
    contents = None
    try:
        host = smtplib.SMTP(app.config['EMAIL_SERVER'], app.config.get('EMAIL_PORT', 25), 'ibcook.com', timeout=2)
        host.set_debuglevel(app.config.get(['EMAIL_DEBUG'], False))
        if app.config.get(['EMAIL_USE_TLS'], False):
            host.starttls()

        host.login(app.config['EMAIL_USERNAME'], app.config['EMAIL_PASSWORD'])

        contents = render_template(template, **kwargs)
        host.sendmail(user.email,
                      app.config['EMAIL_SENDER'],
                      contents)
        return True
    except Exception:
        from traceback import format_exc
        current_app.logger.info(
            "=============================================================\n" +
            "Failed to send mail: {0}\nTO :{1}\n\n\n{2}\n".format(contents, user.email, format_exc()) +
            "=============================================================\n"
        )
        return False


def catch_error_graceful(form=None):
    # grab current exception information
    exc, txt, tb = sys.exc_info()

    def log(msg):
        from pprint import pformat
        from traceback import format_exc
        current_app.logger.warn(
            "=============================================================\n" +
            "{0}\nRequest dump: {1}\n{2}\n".format(msg, pformat(vars(request)), format_exc()) +
            "=============================================================\n"
        )

    if exc is mongoengine.errors.ValidationError:
        if form:
            form.start.add_msg({'message': 'A database schema validation error has occurred. This has been logged with a high priority.'})
        log("A validation occurred.")
    elif exc is mongoengine.errors.InvalidQueryError:
        if form:
            form.start.add_msg({'message': 'A database schema validation error has occurred. This has been logged with a high priority.'})
        log("An inconsistency in the models was detected")
    elif exc is mongoengine.errors.NotUniqueError:
        if form:
            form.start.add_msg({'message': 'A duplication error happended on the datastore side, one of your values is not unique. This has been logged.'})
        log("A duplicate check on the database side was not caught")
    elif exc in (mongoengine.errors.OperationError, mongoengine.errors.DoesNotExist):
        if form:
            form.start.add_msg({'message': 'An unknown database error. This has been logged.'})
        log("An unknown operation error occurred")
    else:
        if form:
            form.start.add_msg({'message': 'An unknown error has occurred'})
        log("")
