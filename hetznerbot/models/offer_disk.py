from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship

from hetznerbot.db import base
from hetznerbot.helper.disk_type import DiskType


class OfferDisk(base):
    """The database model for an offer disk."""

    __tablename__ = "offer_disk"

    id = Column(Integer, primary_key=True)

    type = Column(Enum(DiskType), nullable=False)
    size = Column(SmallInteger, nullable=False)
    amount = Column(SmallInteger, nullable=False)

    offer_id = Column(Integer, ForeignKey("offer.id", ondelete="cascade"), index=True, nullable=False)
    offer = relationship("Offer")

    def __init__(self, offer_id: int, disk_type: DiskType, size: int):
        """Create a new offer disk."""
        self.offer_id = offer_id
        self.type = disk_type
        self.size = size
        self.amount = 1
