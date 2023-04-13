from sqlalchemy import BigInteger, Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from hetznerbot.db import base


class Subscriber(base):
    """The database model for a subscriber."""

    __tablename__ = "subscriber"

    chat_id = Column(BigInteger, primary_key=True)
    active = Column(Boolean, nullable=False, default=True)

    hdd_count = Column(Integer, nullable=False, default=3)
    hdd_size = Column(Integer, nullable=False, default=2048)
    raid = Column(String, default="raid5")
    after_raid = Column(Integer, nullable=False, default=4096)

    cores = Column(Integer, nullable=False, default=4)
    threads = Column(Integer, nullable=False, default=8)
    release = Column(Integer, nullable=False, default=2010)
    multi_rating = Column(Integer, nullable=False, default=5000)
    single_rating = Column(Integer, nullable=False, default=1000)

    price = Column(Integer, nullable=False, default=40)
    ram = Column(Integer, nullable=False, default=16)
    datacenter = Column(String, nullable=True)

    ipv4 = Column(Boolean, nullable=False, server_default="FALSE")
    ecc = Column(Boolean, nullable=False, server_default="FALSE")
    inic = Column(Boolean, nullable=False, server_default="FALSE")
    hwr = Column(Boolean, nullable=False, server_default="FALSE")

    authorized = Column(Boolean, nullable=False, server_default="FALSE", default=False)

    offer_subscriber = relationship(
        "OfferSubscriber", cascade="all", back_populates="subscriber"
    )

    def __init__(self, chat_id):
        """Create a new subscriber."""
        self.chat_id = chat_id

    @staticmethod
    def get_or_create(session, chat_id):
        """Get or create a new subscriber."""
        subscriber = session.get(Subscriber, chat_id)
        if not subscriber:
            subscriber = Subscriber(chat_id)
            session.add(subscriber)
            session.commit()
            subscriber = session.get(Subscriber, chat_id)

        return subscriber
