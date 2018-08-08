"""The sqlite model for a subscriber."""
from hetzner.db import base

from sqlalchemy import Column, String, DateTime, func, Integer, Boolean, Float
from sqlalchemy import ForeignKeyConstraint


class Offer(base):
    """The sqlite model for a subscriber."""

    __tablename__ = 'offer'
    __table_args__ = (
        ForeignKeyConstraint(['chat_id'], ['subscriber.chat_id']),
    )

    id = Column(Integer(), primary_key=True)
    chat_id = Column(String(100), nullable=True)
    cpu = Column(String(100), nullable=False)
    cpu_rating = Column(Integer(), nullable=False)
    ram = Column(Integer(), nullable=False)
    hd_count = Column(Integer(), nullable=False)
    hd_size = Column(Float(), nullable=False)
    ecc = Column(Boolean(), nullable=False, default=False)
    inic = Column(Boolean(), nullable=False, default=False)
    hwr = Column(Boolean(), nullable=False, default=False)
    price = Column(Integer(), nullable=False)
    next_reduction = Column(DateTime())
    last_update = Column(DateTime(), server_default=func.now(), nullable=False)

    def __init__(self, chat_id):
        """Create a new subscriber."""
        self.chat_id = chat_id
