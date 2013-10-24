import argparse
import datetime
import time
import os
import mongoengine
import logging

from weekly.models import User, Post, Comment

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Changes all usernames in the database to lowercase')
    args = parser.parse_args()

    users = User.objects.all()
    for user in users:
        old_uname = user.username
        # Migrate all the posts and comments
        user.username = old_uname.lower()
        user.save()
