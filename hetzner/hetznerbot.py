#!/usr/bin/env python3

from bs4 import BeautifulSoup
from requests import request
from hetzner.config import (
    TELEGRAM_API_KEY,
    MIN_CPU_RATING,
    MIN_HD_COUNT,
    MIN_HD_SIZE,
    MIN_HD_SIZE_RAID,
    MIN_RAM_SIZE,
    MAX_PRICE,
)

from telegram.ext import (
    Filters,
    MessageHandler,
    CommandHandler,
    Updater,
)

attributes = [
    'cpu',
    'cpu_rating',
    'ram',
    'none',
    'price',
    'next_reduction',
]


class Hetzner():
    """A bot which checks if there is a new record in the server section of hetzner

    """
    def __init__(self):
        """Initialize telegram bot and all needed variables."""
        self.subscribers = {}

        self.updater = Updater(token=TELEGRAM_API_KEY)
        dispatcher = self.updater.dispatcher

        # Create jobs
        job_queue = self.updater.job_queue
        job_queue.run_repeating(self.process_all, interval=10, first=0)

        # Create handler
        get_handler = CommandHandler('get', self.get)
        stop_handler = CommandHandler('stop', self.stop)
        start_handler = CommandHandler('start', self.start)

        # Add handler
        dispatcher.add_handler(get_handler)
        dispatcher.add_handler(stop_handler)
        dispatcher.add_handler(start_handler)

        self.updater.start_polling()

    def main(self):
        """The main loop of the bot."""
        self.updater.idle()

    def get(self, bot, update):
        self.process(bot, update.message.chat_id)

    def start(self, bot, update):
        self.subscribers[update.message.chat_id] = True

    def stop(self, bot, update):
        self.subscribers[update.message.chat_id] = False

    def process_all(self, bot, update):
        for chat_id, enabled in self.subscribers.items():
            if enabled:
                self.process(bot, chat_id)

    def process(self, bot, chat_id):
        """Send the newest update to all subscribers."""

        # Extract message meta data
        offers = self.get_hetzner_offers()
        formatted = self.format_offers(offers)
        print(formatted)
        bot.sendMessage(chat_id=chat_id, text=formatted)

    def format_offers(self, offers):
        formatted_offers = []
        for offer in offers:
            formatted = 'Cpu: {} , Rating: {}, Ram: {}, HD: {}, Price: {}'.format(
                offer['cpu'],
                offer['cpu_rating'],
                offer['ram'],
                offer['hd'],
                offer['price'],
            )
            formatted_offers.append(formatted)
        return '\n'.join(formatted_offers)

    def get_hetzner_offers(self):
        """Get the newest hetzner offers."""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://robot.your-server.de/order/market',
            'Origin': 'https://robot.your-server.de',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36',
        }
        data = [
            ('ram', MIN_RAM_SIZE),
            ('hdnr', MIN_HD_COUNT),
            ('hdsize', MIN_HD_SIZE),
            ('maxprice', MAX_PRICE),
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
            if offer['cpu_rating'] < MIN_CPU_RATING:
                continue
            if 'i7-9' in offer['cpu']:
                continue
            if (offer['hd_count'] - 1) * offer['hd_size'] < MIN_HD_SIZE_RAID:
                continue

            offers.append(offer)

        return offers

attributes = [
    'cpu',
    'cpu_rating',
    'ram',
    'hd',
    'price',
    'next_reduction',
]

