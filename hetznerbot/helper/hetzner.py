"""Hetzner helper functions."""
import json
import telegram
import dateparser
from requests import request
from requests.exceptions import ConnectionError

from hetznerbot.sentry import sentry
from hetznerbot.helper.text import split_text
from hetznerbot.models import (
    Offer,
    OfferSubscriber,
    Subscriber,
)


def get_hetzner_offers():
    """Get the newest hetzner offers."""
    headers = {
        "Content-Type": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip,deflate,br",
        "Referer": "https://www.hetzner.de/sb",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36",
    }

    url = "https://www.hetzner.de/a_hz_serverboerse/live_data.json"
    try:
        response = request("GET", url, headers=headers)
        data = json.loads(response.content)
    except ConnectionError:
        print("Connection error while retrieving data.")
        return None

    return data["server"]


def calculate_price(price):
    """Get the brutto price."""
    price = float(price)
    price = price * 1.19
    return int(round(price, 0))


def update_offers(session, incoming_offers):
    """Update all offers and check for updates."""
    ids = []
    offers = []

    for incoming_offer in incoming_offers:
        ids.append(incoming_offer["key"])
        offer = session.query(Offer).get(incoming_offer["key"])

        if not offer:
            offer = Offer(incoming_offer["key"])

        offer.cpu = incoming_offer["cpu"]
        offer.cpu_rating = incoming_offer["cpu_benchmark"]
        offer.ram = incoming_offer["ram"]
        offer.datacenter = incoming_offer["datacenter"][1]

        offer.hdd_count = incoming_offer["hdd_count"]
        offer.hdd_size = incoming_offer["hdd_size"]

        offer.ecc = incoming_offer["is_ecc"]
        offer.inic = "iNIC" in incoming_offer["specials"]
        offer.hwr = "HWR" in incoming_offer["specials"]

        # Notify all subscribers about the price change
        price = calculate_price(incoming_offer["price"])
        if offer.price is not None and offer.price != price:
            for offer_subscriber in offer.offer_subscriber:
                offer_subscriber.notified = False

        offer.price = price
        offer.next_reduction = dateparser.parse(
            "in " + incoming_offer["next_reduce_hr"]
        )

        offer.deactivated = False
        session.add(offer)
        offers.append(offer)

    session.commit()

    # Deactivate all old offers
    session.query(Offer).filter(Offer.deactivated.is_(False)).filter(
        Offer.id.notin_(ids)
    ).update({"deactivated": True}, synchronize_session="fetch")

    return offers


def check_all_offers_for_subscriber(session, subscriber):
    """Check all offers for a specific subscriber."""
    check_offer_for_subscriber(session, subscriber)


def check_offers_for_subscribers(session):
    """Check for each offer if any subscriber are interested in it."""
    subscribers = session.query(Subscriber).filter(Subscriber.active.is_(True)).all()

    for subscriber in subscribers:
        check_offer_for_subscriber(session, subscriber)


def check_offer_for_subscriber(session, subscriber):
    """Check the offers for a specific subscriber."""
    query = (
        session.query(Offer)
        .filter(Offer.deactivated.is_(False))
        .filter(Offer.price <= subscriber.price)
        .filter(Offer.cpu_rating >= subscriber.cpu_rating)
        .filter(Offer.ram >= subscriber.ram)
        .filter(Offer.hdd_count >= subscriber.hdd_count)
        .filter(Offer.hdd_size >= subscriber.hdd_size)
    )

    # Calculate after_raid
    if subscriber.raid == "raid5":
        after_raid = (Offer.hdd_count - 1) * Offer.hdd_size
        query = query.filter(subscriber.after_raid <= after_raid)
    elif subscriber.raid == "raid6":
        after_raid = (Offer.hdd_count - 2) * Offer.hdd_size
        query = query.filter(subscriber.after_raid <= after_raid)

    if subscriber.datacenter is not None:
        match_offers = query.filter(Offer.datacenter != subscriber.datacenter)

    if subscriber.ecc:
        match_offers = query.filter(Offer.ecc.is_(True))

    if subscriber.inic:
        match_offers = query.filter(Offer.inic.is_(True))

    if subscriber.hwr:
        match_offers = query.filter(Offer.hwr.is_(True))

    matching_offers = query.all()

    for offer in matching_offers:
        # There is no relation yet. Create a new OfferSubscriber entity
        exists = list(
            filter(lambda o: o.offer_id == offer.id, subscriber.offer_subscriber)
        )

        if len(exists) == 0:
            offer_subscriber = OfferSubscriber(offer.id, subscriber.chat_id)
            subscriber.offer_subscriber.append(offer_subscriber)
            session.add(offer_subscriber)

        session.commit()

    # Clean old entries
    for offer_subscriber in subscriber.offer_subscriber:
        if offer_subscriber.offer not in matching_offers:
            session.delete(offer_subscriber)

    session.commit()


def format_offers(offer_subscriber, get_all=False):
    """Format the found offers."""
    # Filter all offers, which aren't notified yet, if the user doesn't want all offers.
    if not get_all:
        offer_subscriber = list(filter(lambda o: not o.notified, offer_subscriber))

    if len(offer_subscriber) == 0:
        return []

    formatted_offers = ["All offers:" if get_all else "New offers:"]
    for i, offer_subscriber in enumerate(offer_subscriber):
        # The subscriber should only receive new offers
        offer_subscriber.notified = True
        offer = offer_subscriber.offer

        # Format next reduction
        if offer.next_reduction is not None:
            next_reduction = offer.next_reduction
        else:
            next_reduction = "Fixed Price"

        # Format extra features
        extra_features = ""
        if offer.ecc:
            extra_features += "ECC "
        if offer.inic:
            extra_features += "iNIC "
        if offer.hwr:
            extra_features += "HWR "
        if extra_features == "":
            extra_features = "None"

        formatted_offer = """Offer {0}
Cpu: {1} with rating {2}
Ram: {3} GB
HD: {4} drives with {5} GB Capacity ({6}GB total)
Extra features: {7}
Price: {8}
Datacenter: {9}
Next price reduction: {10}""".format(
            i,
            offer.cpu,
            offer.cpu_rating,
            offer.ram,
            offer.hdd_count,
            offer.hdd_size,
            offer.hdd_size * offer.hdd_count,
            extra_features,
            offer.price,
            offer.datacenter,
            next_reduction,
        )
        formatted_offers.append(formatted_offer)

    formatted_offers = split_text(formatted_offers, max_chunks=5)

    return formatted_offers


def send_offers(bot, subscriber, session, get_all=False):
    """Send the newest update to all subscribers."""
    # Extract message meta data
    if get_all:
        formatted_offers = format_offers(subscriber.offer_subscriber, get_all=True)
    else:
        formatted_offers = format_offers(subscriber.offer_subscriber)

    if len(formatted_offers) > 0:
        for chunk in formatted_offers:
            try:
                bot.sendMessage(
                    chat_id=subscriber.chat_id, text=chunk,
                )
            except telegram.error.Unauthorized:
                session.delete(subscriber)
                session.commit()

        if formatted_offers == 5:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                text="Too many results, please narrow down your search a little.",
            )
    else:
        if get_all:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                text="There are currently no offers for your criteria.",
            )
