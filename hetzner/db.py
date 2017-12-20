"""Helper class to get a database engine and to get a session."""
from hetzner.config import SQL_URI
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(SQL_URI, poolclass=NullPool)
base = declarative_base(bind=engine)


def get_session(connection=None):
    """Get a new db session."""
    session = sessionmaker(bind=engine)
    if connection:
        return session(bind=connection)
    return session()
