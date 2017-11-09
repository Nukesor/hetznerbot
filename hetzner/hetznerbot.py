"""The actual bot."""

import datetime
from bs4 import BeautifulSoup
from requests import request
from hetzner.config import TELEGRAM_API_KEY
from hetzner.db import get_session
from hetzner.offer import Offer
from hetzner.subscriber import Subscriber

from telegram.ext import (
    CommandHandler,
    Updater,
)

attributes = [
    'cpu',
    'cpu_rating',
    'ram',
    'hd',
    'price',
    'next_reduction',
]


class Hetzner():
    """A bot which checks if there is a new record in the server section of hetzner."""

    def __init__(self):
        """Initialize telegram bot and all needed variables."""
        self.updater = Updater(token=TELEGRAM_API_KEY)
        dispatcher = self.updater.dispatcher

        # Create jobs
        job_queue = self.updater.job_queue
        job_queue.run_repeating(self.process_all, interval=600, first=0)

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
        help_text = """A nice little telegram bot, which texts you,
        if there are any offers on the hetzner server market,
        that match your defined criteria.

        Available commands:
        /start Start the bot
        /stop Start the bot
        /set Set attributes with this syntax: "\set hd_count 3"
            Attributes are:
                - `hd_count`    int (Number of hard drives)
                - `hd_size`      int (Minimum for each disk in GB)
                - `raid`            enum ('raid5', 'raid6', 'None')
                - `after_raid`   int (Size after raid assembly in TB)
                - `cpu_rating`  int
                - `ram`             int (RAM size in GB)
                - `price`           int (Price in Euro)
        /get Check hetzner now!
        /info Get the current attributes.
        /help Show this text
        """
        bot.sendMessage(chat_id=update.message.chat_id, text=help_text)

    def info(self, bot, update):
        """Get the newest hetzner offers."""
        session = get_session()
        chat_id = update.message.chat_id
        subscriber = self.get_or_create_subscriber(session, chat_id)

        formatted = ' hd_count: {0}\n hd_size: {1} GB\n raid: {2}\n after_raid: {3} TB\n cpu_rating: {4}\n ram: {5} GB\n price: {6} Euro'.format(
                subscriber.hd_count,
                subscriber.hd_size,
                subscriber.raid,
                subscriber.after_raid,
                subscriber.cpu_rating,
                subscriber.ram,
                subscriber.price,
            )
        session.close()
        bot.sendMessage(chat_id=chat_id, text=formatted)

    def get(self, bot, update):
        """Get the newest hetzner offers."""
        session = get_session()
        subscriber = self.get_or_create_subscriber(
            session, update.message.chat_id)
        self.process(bot, subscriber, session=session, get_all=True)
        session.close()

    def set(self, bot, update):
        """Set query attributes."""
        session = get_session()
        chat_id = update.message.chat_id
        subscriber = self.get_or_create_subscriber(
            session, chat_id)

        text = update.message.text
        field = text.split(' ')[1:]

        fields = ['hd_count', 'hd_size', 'raid', 'after_raid',
                  'cpu_rating', 'ram', 'price']

        if field[0] not in fields:
            bot.sendMessage(chat_id=chat_id, text='Invalid field. Type /help for more information')
            return

        if field[0] == 'raid':
            if field[1] not in ['raid5', 'raid6']:
                if field[1] == 'None':
                    field[1] = None
                else:
                    bot.sendMessage(
                        chat_id=chat_id,
                        text='Invalid value for "raid". Type /help for more information',
                    )
        else:
            try:
                field[1] = int(field[1])
            except BaseException as e:
                bot.sendMessage(
                    chat_id=chat_id,
                    text='Value is not an int.',
                )

        setattr(subscriber, field[0], field[1])
        session.add(subscriber)
        session.commit()
        session.close()

    def start(self, bot, update):
        """Start the bot."""
        session = get_session()
        chat_id = update.message.chat_id

        subscriber = self.get_or_create_subscriber(session, chat_id)
        subscriber.active = True
        session.add(subscriber)
        session.commit()
        session.close()

        text = 'You will now receive offers. Type /help for more info.'
        bot.sendMessage(chat_id=chat_id, text=text)

    def stop(self, bot, update):
        """Stop the bot."""
        session = get_session()
        chat_id = update.message.chat_id

        subscriber = self.get_or_create_subscriber(session, chat_id)
        subscriber.active = False
        session.add(subscriber)
        session.commit()
        session.close()

        text = "You won't receive any more offers."
        bot.sendMessage(chat_id=chat_id, text=text)

    def process_all(self, bot, job):
        """Check for every subscriber."""
        session = get_session()
        subscribers = session.query(Subscriber) \
            .filter(Subscriber.active == True) \
            .all()
        for subscriber in subscribers:
            self.process(bot, subscriber, session=session)
        session.close()

    def process(self, bot, subscriber, session, get_all=False):
        """Send the newest update to all subscribers."""
        # Extract message meta data
        offers = self.get_hetzner_offers(subscriber)
        new_offers = []
        for offer in offers:
            db_offer = session.query(Offer) \
                .filter(Offer.chat_id == subscriber.chat_id) \
                .filter(Offer.cpu == offer['cpu']) \
                .filter(Offer.cpu_rating == offer['cpu_rating']) \
                .filter(Offer.ram == offer['ram']) \
                .filter(Offer.hd == offer['hd']) \
                .filter(Offer.price == offer['price']) \
                .one_or_none()
            if not db_offer:
                new_offers.append(offer)
                db_offer = Offer(subscriber.chat_id, offer['cpu'],
                    offer['cpu_rating'], offer['ram'], offer['hd'],
                    offer['price'], offer['next_reduction'])
                session.add(db_offer)
                session.commit()
            else:
                db_offer.last_update = datetime.datetime.now()

            session.add(db_offer)

        end_date = datetime.datetime.now() - datetime.timedelta(minutes=1)
        session.query(Offer) \
            .filter(Offer.chat_id == subscriber.chat_id) \
            .filter(Offer.last_update < end_date) \
            .delete()
        session.commit()

        if get_all:
            formatted = self.format_offers(offers)
        else:
            formatted = self.format_offers(new_offers)

        if formatted:
            bot.sendMessage(
                chat_id=subscriber.chat_id,
                text=formatted,
            )

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
        response = request('POST', url, data=data, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all items
        items = soup.find_all('div', 'box_sm')
        for item in items:
            # Create an offer of each item.
            offer = {}
            details = item.table.tr.find_all('td')
            for key, detail in enumerate(details):
                if len(list(detail.children)) > 1:
                    detail = list(detail.children)[0]
                offer[attributes[key]] = detail.string.strip()

            # Formatting
            offer['cpu_rating'] = int(offer['cpu_rating'])
            offer['ram'] = int(offer['ram'].split(' ')[0])
            hd_details = [int(s) for s in offer['hd'].split() if s.isdigit()]
            offer['hd_count'] = hd_details[0]
            offer['hd_size'] = hd_details[1]

            # Filter
            if offer['cpu_rating'] < subscriber.cpu_rating:
                continue
            if 'i7-9' in offer['cpu']:
                continue
            if subscriber.raid == 'raid5':
                if (offer['hd_count'] - 1) * offer['hd_size'] < subscriber.after_raid:
                    continue
            elif subscriber.raid == 'raid6':
                if (offer['hd_count'] - 2) * offer['hd_size'] < subscriber.after_raid:
                    continue

            offers.append(offer)

        return offers

    def format_offers(self, offers):
        """Format the found offers."""
        formatted_offers = []
        for offer in offers:
            formatted = 'Cpu: {0} , Rating: {1}, Ram: {2} GB, HD: {3}, Price: {4}, Next price reduction: {5}'.format(
                offer['cpu'],
                offer['cpu_rating'],
                offer['ram'],
                offer['hd'],
                offer['price'],
                offer['next_reduction'],
            )
            formatted_offers.append(formatted)
        return '\n'.join(formatted_offers)

    def get_or_create_subscriber(self, session, chat_id):
        """Get or create a new subscriber."""
        subscriber = session.query(Subscriber).get(chat_id)
        if not subscriber:
            subscriber = Subscriber(chat_id)
            session.add(subscriber)
            session.commit()
            subscriber = session.query(Subscriber).get(chat_id)

        return subscriber
