"""The sqlite model for a subscriber."""
from hetzner.db import base

from sqlalchemy import Column, String, Integer, Boolean


class Subscriber(base):
    """The sqlite model for a subscriber."""

    __tablename__ = 'subscriber'

    chat_id = Column(String(100), primary_key=True)
    active = Column(Boolean(), nullable=False, default=True)
    hd_count = Column(Integer(), nullable=False, default=3)
    cpu_rating = Column(Integer(), nullable=False, default=8500)
    hd_size = Column(Integer(), nullable=False, default=2048)
    raid = Column(String(10), default='raid5')
    after_raid = Column(Integer(), nullable=False, default=4)
    ram = Column(Integer(), nullable=False, default=16)
    ecc = Column(Boolean(), nullable=False, default=False)
    inic = Column(Boolean(), nullable=False, default=False)
    hwr = Column(Boolean(), nullable=False, default=False)
    price = Column(Integer(), nullable=False, default=40)

    def __init__(self, chat_id):
        """Create a new subscriber."""
        self.chat_id = chat_id
