from sqlalchemy import Column, Integer, String

from hetznerbot.db import base


class Cpu(base):
    """The database model for a cpu."""

    __tablename__ = "cpu"

    name = Column(String, nullable=False, primary_key=True)
    cores = Column(Integer, nullable=True)
    threads = Column(Integer, nullable=True)
    release = Column(Integer, nullable=True)
    multi_thread_rating = Column(Integer, nullable=True)
    single_thread_rating = Column(Integer, nullable=True)

    def __init__(self, name):
        """Create a new cpu."""
        self.name = name
