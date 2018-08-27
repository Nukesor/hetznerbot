"""The actual bot."""

import traceback
import datetime
import dateparser
import telegram
from bs4 import BeautifulSoup
from requests import request
from requests.exceptions import ConnectionError
from hetzner.config import config
from hetzner.db import get_session
from hetzner.offer import Offer
from hetzner.sentry import Sentry
from hetzner.subscriber import Subscriber
from hetzner.helper import (
    help_text,
    is_int_or_float,
    int_or_float,
)

from telegram.ext import (
    CommandHandler,
    Updater,
)


class Hetzner():
    """A bot which checks if there is a new record in the server section of hetzner."""

    def __init__(self):
        """Initialize telegram bot and all needed variables."""
        # Initialize sentry
        self.sentry = Sentry()

        # Initialize telegram updater and dispatcher
        self.updater = Updater(token=config.TELEGRAM_API_KEY)
        dispatcher = self.updater.dispatcher

        # Create jobs
        job_queue = self.updater.job_queue
        job_queue.run_repeating(self.process_all, interval=120, first=0)

        # Create handler
        help_handler = CommandHandler('help', self.help)
        get_handler = CommandHandler('get', self.get)
        set_handler = CommandHandler('set', self.set)
        info_handler = CommandHandler('info', self.info)
        stop_handler = CommandHandler('stop', self.stop)
        start_handler = CommandHandler('start', self.start)

        # Add handler
        dispatcher.add_handler(help_handler)
        dispatcher.add_handler(info_handler)
        dispatcher.add_handler(get_handler)
        dispatcher.add_handler(set_handler)
        dispatcher.add_handler(stop_handler)
        dispatcher.add_handler(start_handler)

        self.updater.start_polling()

    def main(self):
        """Update loop of the bot."""
        self.updater.idle()

    def help(self, bot, update):
        """Send a help text."""
        bot.sendMessage(chat_id=update.message.chat_id, text=help_text)

    def info(self, bot, update):
        """Get the newest hetzner offers."""
        session = get_session()
        try:
            chat_id = update.message.chat_id
            subscriber = Subscriber.get_or_create(session, chat_id)

            formatted = """hd_count: {0}
hd_size: {1} GB
raid: {2}
after_raid: {3} TB
cpu_rating: {4}
ecc: {5}
inic: {6}
hwr: {7}
ram: {8} GB
price: {9} Euro""".format(
                    subscriber.hd_count,
                    subscriber.hd_size,
                    subscriber.raid,
                    subscriber.after_raid,
                    subscriber.cpu_rating,
                    subscriber.ecc,
                    subscriber.inic,
                    subscriber.hwr,
                    subscriber.ram,
                    subscriber.price,
                )
            bot.sendMessage(chat_id=chat_id, text=formatted)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def get(self, bot, update):
        """Get the newest hetzner offers."""
        session = get_session()
        try:
            subscriber = Subscriber.get_or_create(session, update.message.chat_id)
            self.process(bot, subscriber, session=session, get_all=True)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def set(self, bot, update):
        """Set query attributes."""
        session = get_session()
        try:
            chat_id = update.message.chat_id
            subscriber = Subscriber.get_or_create(session, chat_id)

            text = update.message.text
            parameters = text.split(' ')[1:]

            parameter_names = ['hd_count', 'hd_size', 'raid', 'after_raid',
                               'cpu_rating', 'ram', 'price', 'ecc', 'inic', 'hwr']

            # We need exactly two parameter. Name and value
            if len(parameters) != 2:
                bot.sendMessage(chat_id=chat_id, text='Exactly two parameter need to be specified.')
                return

            [name, value] = parameters

            # Check if we know this parameter
            if name not in parameter_names:
                bot.sendMessage(chat_id=chat_id, text='Invalid parameter. Type /help for more information')
                return

            # validate raid choices
            if name == 'raid':
                if value not in ['raid5', 'raid6']:
                    if value == 'None':
                        value = None
                    else:
                        bot.sendMessage(chat_id=chat_id, text='Invalid value for "raid". Type /help for more information')
                        return
                elif value == 'raid5' == subscriber.hd_count < 3 \
                        or value == 'raid6' == subscriber.hd_count < 4:
                    bot.sendMessage(chat_id=chat_id,
                                    text='Invalid raid type for current hd_count. RAID5 needs at least 3 drives, RAID6 needs at least 4 drives')
            # Validate int values
            else:
                try:
                    value = int(value)
                except BaseException as e:
                    bot.sendMessage(
                        chat_id=chat_id,
                        text='Value is not an int.',
                    )
                    return

            # Validate boolean values
            if name in ['ecc', 'inic', 'hwr']:
                if value not in [0, 1]:
                    bot.sendMessage(chat_id=chat_id, text='The value needs to be a boolean (0 or 1)')
                    return

                setattr(subscriber, name, bool(value))

            setattr(subscriber, name, value)
            session.add(subscriber)
            session.commit()

            self.process(bot, subscriber, session=session)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def start(self, bot, update):
        """Start the bot."""
        session = get_session()
        try:
            chat_id = update.message.chat_id

            subscriber = Subscriber.get_or_create(session, chat_id)
            subscriber.active = True
            session.add(subscriber)
            session.commit()

            text = 'You will now receive offers. Type /help for more info.'
            bot.sendMessage(chat_id=chat_id, text=text)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def stop(self, bot, update):
        """Stop the bot."""
        session = get_session()
        try:
            chat_id = update.message.chat_id

            subscriber = Subscriber.get_or_create(session, chat_id)
            subscriber.active = False
            session.add(subscriber)
            session.commit()

            text = "You won't receive any more offers."
            bot.sendMessage(chat_id=chat_id, text=text)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def process_all(self, bot, job):
        """Check for every subscriber."""
        session = get_session()
        try:
            subscribers = session.query(Subscriber) \
                .filter(Subscriber.active == True) \
                .all()
            for subscriber in subscribers:
                self.process(bot, subscriber, session=session)
        except BaseException as e:
            traceback.print_exc()
        finally:
            session.remove()

    def process(self, bot, subscriber, session, get_all=False):
        """Send the newest update to all subscribers."""
        # Extract message meta data
        offers = self.get_hetzner_offers(subscriber)
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
            formatted = self.format_offers(offers)
        else:
            if len(new_offers) == 0:
                return
            formatted = self.format_offers(new_offers)

        if formatted:
            try:
                bot.sendMessage(
                    chat_id=subscriber.chat_id,
                    text=formatted,
                )
            except telegram.error.Unauthorized:
                session.delete(subscriber)
                session.commit()

    def get_hetzner_offers(self, subscriber):
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

    def format_offers(self, offers):
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
