"""The sqlite model for a subscriber."""
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func
from sqlalchemy.orm import relationship

from hetznerbot.db import base


class Offer(base):
    """The sqlite model for an offer."""

    __tablename__ = "offer"

    id = Column(Integer, primary_key=True)
    deactivated = Column(Boolean, nullable=False, server_default="FALSE")

    cpu = Column(String, nullable=False)
    ram = Column(Integer, nullable=False)
    datacenter = Column(String, nullable=True)

    hdd_count = Column(Integer, nullable=False)
    hdd_size = Column(Float, nullable=False)

    # Specials
    ecc = Column(Boolean, nullable=False, server_default="FALSE")
    inic = Column(Boolean, nullable=False, server_default="FALSE")
    hwr = Column(Boolean, nullable=False, server_default="FALSE")
    ipv4 = Column(Boolean, nullable=False, server_default="FALSE")

    # Save the net price in cents
    price = Column(Integer, nullable=False)
    last_update = Column(DateTime, server_default=func.now(), nullable=False)

    offer_subscriber = relationship("OfferSubscriber", back_populates="offer")

    def __init__(self, offer_id):
        """Create a new subscriber."""
        self.id = offer_id
