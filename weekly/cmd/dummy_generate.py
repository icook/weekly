import argparse
import datetime
import time
import os
import mongoengine
import logging

from loremipsum import get_paragraphs, get_sentences

from weekly.models import User, Post, Team

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add lipsum to posts data for testing')
    parser.add_argument('go', help='Must equal exactly "true" to avoid accidents')
    args = parser.parse_args()

    if args.go == "true":
        now = datetime.datetime.now().isocalendar()
        week = now[1] - 1
        year = now[0]


        for i in range(-3, 3):

            for team in Team.objects.all():
                if team.text == "Other":
                    continue

                for user in team.users():
                    try:
                        pst = Post.objects.get(user=user, week=week+i, year=year)
                        pst.delete()
                    except Post.DoesNotExist:
                        pass
                    pst = Post(user=user, week=week+i, year=year, body='\n\n'.join(get_paragraphs(3)))
                    pst.save()

