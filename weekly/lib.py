import datetime

def get_now():
    return datetime.datetime.now() - datetime.timedelta(hours=4)

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
