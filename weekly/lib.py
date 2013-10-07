import datetime
import time

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
