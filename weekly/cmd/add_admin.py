import argparse
import datetime
import time
import os
import mongoengine
import logging

from weekly.models import User

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add a new admin to the system')
    parser.add_argument('username', help='the name of the user to make an admin')
    args = parser.parse_args()

    try:
        usr = User.objects.get(username=args.username)
    except User.DoesNotExist:
        logging.error("User doesn't exist")
    else:
        usr.active = True
        usr.admin = True
        usr.save()
