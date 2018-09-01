#!/bin/env python
"""Drop and create a new database with schema."""

from sqlalchemy_utils.functions import database_exists, create_database, drop_database
from hetzner.db import engine, base
from hetzner.subscriber import Subscriber # noqa
from hetzner.offer import Offer # noqa


db_url = engine.url
if database_exists(db_url):
    drop_database(db_url)
create_database(db_url)

base.metadata.drop_all()
base.metadata.create_all()
