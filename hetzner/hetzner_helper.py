"""Hetzner helper functions."""
import datetime
import dateparser
import telegram
from bs4 import BeautifulSoup
from requests import request
from requests.exceptions import ConnectionError

from hetzner.offer import Offer
from hetzner.helper import (
    is_int_or_float,
    int_or_float,
)


def process(bot, subscriber, session, get_all=False):
    """Send the newest update to all subscribers."""
    # Extract message meta data
    offers = get_hetzner_offers(subscriber)
    new_offers = []
    for offer in offers:
        existing_offer = session.query(Offer) \
            .filter(Offer.chat_id == subscriber.chat_id) \
            .filter(Offer.cpu == offer.cpu) \
            .filter(Offer.cpu_rating == offer.cpu_rating) \
            .filter(Offer.ram == offer.ram) \
            .filter(Offer.hd_count == offer.hd_count) \
            .filter(Offer.hd_size == offer.hd_size) \
            .filter(Offer.price == offer.price) \
            .filter(Offer.ecc == offer.ecc) \
            .one_or_none()

        # Either add new offer or update existing offer
        if not existing_offer:
            new_offers.append(offer)
        else:
            offer = existing_offer

        # Set the last update time and commit the offer it
        offer.last_update = datetime.datetime.now()
        session.add(offer)
        session.commit()

    # Remove old offers.
    clean_threshold = datetime.datetime.now() - datetime.timedelta(minutes=5)
    session.query(Offer) \
        .filter(Offer.chat_id == subscriber.chat_id) \
        .filter(Offer.last_update < clean_threshold) \
        .delete()
    session.commit()

    if get_all:
        if len(offers) == 0:
            return
        formatted = format_offers(offers)
    else:
        if len(new_offers) == 0:
            return
        formatted = format_offers(new_offers)

    if formatted:
        try:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                text=formatted,
            )
        except telegram.error.Unauthorized:
            session.delete(subscriber)
            session.commit()


def get_hetzner_offers(subscriber):
    """Get the newest hetzner offers."""
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://robot.your-server.de/order/market',
        'Origin': 'https://robot.your-server.de',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36',
    }

    data = [
        ('ram', subscriber.ram),
        ('hdnr', subscriber.hd_count),
        ('hdsize', subscriber.hd_size),
        ('maxprice', subscriber.price),
        ('text', ''),
        ('datacenter', ''),
    ]

    offers = []

    url = "https://robot.your-server.de/order/market"
    try:
        response = request('POST', url, data=data, headers=headers)
    except ConnectionError:
        print("Got an ConnectionError during hetzner request")
        return {}
    soup = BeautifulSoup(response.content, 'html.parser')

    # Available attributes in hetzner offer table
    # The hd column contains extras such as ECC and HWR.
    attributes = [
        'cpu',
        'cpu_rating',
        'ram',
        'hd',
        'price',
        'next_reduction',
    ]

    # Find all items
    items = soup.find_all('div', 'box_sm')
    for item in items:
        # Create an offer of each item.
        offer = Offer(subscriber.chat_id)
        offer_data = {}
        extra_features = ''

        details = item.table.tr.find_all('td')
        for key, detail in enumerate(details):
            for child in detail.children:
                if isinstance(child, str):
                    offer_data[attributes[key]] = child.strip()
                elif child.name == 'span' and attributes[key] == 'hd':
                    extra_features = child.string.strip()
                elif child.name == 'span':
                    offer_data[attributes[key]] = child.string.strip()

        offer.cpu = offer_data['cpu']
        # Formatting simple integer values
        offer.cpu_rating = int(offer_data['cpu_rating'])
        offer.ram = int(offer_data['ram'].split(' ')[0])

        # Extracting the hd size and count.
        hd_details = [int_or_float(s) for s in offer_data['hd'].split() if is_int_or_float(s)]
        offer.hd_count = hd_details[0]
        offer.hd_size = hd_details[1]

        # Extracting extra features
        offer.ecc = 'ECC' in extra_features
        offer.inic = 'INIC' in extra_features
        offer.hwr = 'HWR' in extra_features

        offer.price = offer_data['price']

        offer.next_reduction = dateparser.parse('in ' + offer_data['next_reduction'])

        # Filter cpu rating
        if offer.cpu_rating < subscriber.cpu_rating:
            continue

        # Filter invalid raid count
        if subscriber.raid == 'raid5':
            if (offer.hd_count - 1) * offer.hd_size < subscriber.after_raid:
                continue
        elif subscriber.raid == 'raid6':
            if (offer.hd_count - 2) * offer.hd_size < subscriber.after_raid:
                continue

        # Filter ecc, hwr and inic
        if subscriber.inic and not offer.inic \
                or subscriber.hwr and not offer.hwr \
                or subscriber.ecc and not offer.ecc:
            continue

        offers.append(offer)

    return offers


def format_offers(offers):
    """Format the found offers."""
    formatted_offers = 'New offers:'
    for i, offer in enumerate(offers):
        if offer.next_reduction is not None:
            next_reduction = offer.next_reduction
        else:
            next_reduction = 'Fixed Price'

        extra_features = ''
        if offer.ecc:
            extra_features += 'ECC '
        if offer.inic:
            extra_features += 'iNIC '
        if offer.hwr:
            extra_features += 'HWR '
        if extra_features == '':
            extra_features = 'None'

        formatted_offer = """\n\nOffer {0}
Cpu: {1} with rating {2}
Ram: {3} GB
HD: {4} drives with {5} TB Capacity ({6}TB total)
Extra features: {7}
Price: {8}
Next price reduction: {9}""".format(
            i,
            offer.cpu,
            offer.cpu_rating,
            offer.ram,
            offer.hd_count,
            offer.hd_size,
            offer.hd_size * offer.hd_count,
            extra_features,
            offer.price,
            next_reduction,
        )
        formatted_offers += formatted_offer
    return formatted_offers
