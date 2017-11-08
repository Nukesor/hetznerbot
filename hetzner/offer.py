"""The sqlite model for a subscriber."""
from hetzner.db import base

from sqlalchemy import Column, String, DateTime, func, Integer
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
    cpu_rating = Column(String(100), nullable=False)
    ram = Column(String(100), nullable=False)
    hd = Column(String(100), nullable=False)
    price = Column(String(100), nullable=False)
    next_reduction = Column(String(100), nullable=False)
    last_update = Column(DateTime(), server_default=func.now(), nullable=False)

    def __init__(self, chat_id, cpu, cpu_rating, ram, hd, price, reduction):
        """Create a new subscriber."""
        self.chat_id = chat_id
        self.cpu = cpu
        self.cpu_rating = cpu_rating
        self.ram = ram
        self.hd = hd
        self.price = price
        self.next_reduction = reduction
