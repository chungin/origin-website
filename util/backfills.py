import os
import argparse
from app import app_config
from config import constants

from database import db
from flask import Flask
from tasks import full_contact_request

from logic.emails import email_types

flask_app = Flask(__name__)

flask_app.config.update(
    broker_url=os.environ['REDIS_URL'],
    result_backend=os.environ['REDIS_URL'],
    task_always_eager=os.environ.get('CELERY_DEBUG', False)
)

app_config.init_prod_app(flask_app)

def backfill_presale(limit=100000):
    with flask_app.app_context():
        unfilled = """
            SELECT DISTINCT presale.email
            FROM presale
                LEFT JOIN fullcontact ON presale.email = fullcontact.email
            WHERE fullcontact.id IS NULL
            LIMIT %d
        """ % (limit)
        result = db.engine.execute(unfilled)

        for row in result:
            full_contact_request(row[0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill missing data')

    parser.add_argument('-l', '--limit', default=100000, type=int,
                        help='number of rows it will attempt (default: find the max)')

    args = parser.parse_args()

    backfill_presale(args.limit)