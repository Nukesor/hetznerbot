from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from hetznerbot.db import base


class OfferSubscriber(base):
    """The database model for the relationship between offers and subscribers."""

    __tablename__ = "offer_subscriber"
    __table_args__ = (
        UniqueConstraint("offer_id", "subscriber_id", name="uniq_offer_subscriber"),
    )

    id = Column(Integer, primary_key=True)
    offer_id = Column(
        Integer, ForeignKey("offer.id", ondelete="cascade"), index=True, nullable=False
    )
    subscriber_id = Column(
        BigInteger,
        ForeignKey("subscriber.chat_id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    notified = Column(Boolean, server_default="FALSE", default=False, nullable=False)
    new = Column(Boolean, server_default="FALSE", default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    offer = relationship("Offer")
    subscriber = relationship("Subscriber")

    def __init__(self, offer_id, subscriber_id):
        """Create a new offer_subscriber instance."""
        self.offer_id = offer_id
        self.subscriber_id = subscriber_id
