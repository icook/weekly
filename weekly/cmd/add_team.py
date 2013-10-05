import argparse
import datetime
import time
import os
import mongoengine
import logging

from weekly.models import Team

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add a new team to the list')
    parser.add_argument('teamname', help='the name of the team')
    args = parser.parse_args()

    try:
        team = Team.objects.get(text=args.teamname)
    except Team.DoesNotExist:
        team = Team(text=args.teamname)
        team.save()
    else:
        logging.error("Team already exists")
