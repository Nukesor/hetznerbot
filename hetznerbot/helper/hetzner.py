"""Hetzner helper functions."""
import json
import time
from json import JSONDecodeError

import dateparser
import telegram
from requests import request
from requests.exceptions import ConnectionError

from hetznerbot.helper.text import split_text
from hetznerbot.models import Offer, OfferSubscriber, Subscriber
from hetznerbot.sentry import sentry


def get_hetzner_offers():
    """Get the newest hetzner offers."""
    headers = {
        "Content-Type": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip,deflate,br",
        "Referer": "https://www.hetzner.de/sb",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36",
    }

    # Hetzner expects a millisecond unix timestamp at the end
    unix_timestamp = int(time.time() * 1000)
    url = f"https://www.hetzner.com/_resources/app/jsondata/live_data_sb.json?m={unix_timestamp}"
    try:
        response = request("GET", url, headers=headers)
        data = json.loads(response.content)
        return data["server"]
    except ConnectionError:
        print("Connection error while retrieving data.")
        return None
    except JSONDecodeError:
        sentry.capture_exception()
        return None


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
        offer.ram = incoming_offer["ram_size"]
        offer.datacenter = incoming_offer["datacenter"]

        offer.hdd_count = incoming_offer["hdd_count"]
        offer.hdd_size = incoming_offer["hdd_size"]

        offer.ecc = incoming_offer["is_ecc"]
        offer.inic = "iNIC" in incoming_offer["specials"]
        offer.hwr = "HWR" in incoming_offer["specials"]

        # Notify all subscribers about the price change
        price = int(float(incoming_offer["price"]))
        if offer.price is not None and offer.price != price:
            for offer_subscriber in offer.offer_subscriber:
                offer_subscriber.notified = False

        offer.price = price

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
        query = query.filter(Offer.datacenter != subscriber.datacenter)

    if subscriber.ecc:
        query = query.filter(Offer.ecc.is_(True))

    if subscriber.inic:
        query = query.filter(Offer.inic.is_(True))

    if subscriber.hwr:
        query = query.filter(Offer.hwr.is_(True))

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


def format_offers(subscriber, offer_subscriber, get_all=False):
    """Format the found offers."""
    # Filter all offers, which aren't notified yet, if the user doesn't want all offers.
    if not get_all:
        offer_subscriber = list(filter(lambda o: not o.notified, offer_subscriber))

    if len(offer_subscriber) == 0:
        return []

    formatted_offers = []
    for _, offer_subscriber in enumerate(offer_subscriber):
        # The subscriber should only receive new offers
        offer_subscriber.notified = True
        offer = offer_subscriber.offer

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

        if subscriber.raid == "raid5":
            size = offer.hdd_size * (offer.hdd_count - 1)
            final_size = f"{size}GB post-raid5"
        elif subscriber.raid == "raid6":
            size = offer.hdd_size * (offer.hdd_count - 2)
            final_size = f"{size}GB post-raid6"
        else:
            size = offer.hdd_size * offer.hdd_count
            final_size = f"{size}GB total"

        vat_incl_price = float(offer.price) * 1.19
        formatted_offer = f"""*Offer {offer.id}:*
_Cpu:_ {offer.cpu}
_Ram:_ *{offer.ram} GB*
_HD:_ {offer.hdd_count} drives with *{offer.hdd_size} GB* Capacity *({final_size})*
_Extra features:_ *{extra_features}*
_Price:_ {offer.price}€ (VAT incl.: {vat_incl_price:.2f})
_Datacenter:_ {offer.datacenter}"""

        formatted_offers.append(formatted_offer)

    formatted_offers = split_text(formatted_offers, max_chunks=5)

    return formatted_offers


def send_offers(bot, subscriber, session, get_all=False):
    """Send the newest update to all subscribers."""
    # Extract message meta data
    if get_all:
        formatted_offers = format_offers(
            subscriber, subscriber.offer_subscriber, get_all=True
        )
    else:
        formatted_offers = format_offers(subscriber, subscriber.offer_subscriber)

    if len(formatted_offers) > 0:
        for chunk in formatted_offers:
            try:
                bot.sendMessage(
                    chat_id=subscriber.chat_id,
                    text=chunk,
                    parse_mode="Markdown",
                )
            except telegram.error.Unauthorized:
                session.delete(subscriber)
                session.commit()

        if formatted_offers == 5:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                text="Too many results, please narrow down your search a little.",
            )
            return
    else:
        if get_all:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                parse_mode="Markdown",
                text="There are currently no offers for your criteria.",
            )
