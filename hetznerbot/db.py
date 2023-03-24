"""Helper class to get a database engine and to get a session."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session
from sqlalchemy.orm.session import sessionmaker

from hetznerbot.config import config

engine = create_engine(config["database"]["sql_uri"])
base = declarative_base()


def get_session():
    """Get a new db session."""
    session = scoped_session(sessionmaker(bind=engine))
    return session
