from sqlalchemy import Column, Integer, String

from hetznerbot.db import base


class Cpu(base):
    """The database model for a cpu."""

    __tablename__ = "cpu"

    cpu_name = Column(String, nullable=False, primary_key=True)
    threads = Column(Integer, nullable=False)
    release_date = Column(Integer, nullable=False)
    multi_thread_rating = Column(Integer, nullable=False)
    single_thread_rating = Column(Integer, nullable=False)

    def __init__(self, name):
        """Create a new cpu."""
        self.name = name
