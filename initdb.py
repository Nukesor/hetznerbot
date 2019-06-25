#!/bin/env python
"""Create new database and schema, if it doesn't exist."""
from sqlalchemy_utils.functions import database_exists, create_database
from hetznerbot.db import engine, base
from hetznerbot.models import * # noqa


db_url = engine.url
if not database_exists(db_url):
    create_database(db_url)

    base.metadata.create_all()
