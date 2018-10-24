"""A bot which checks if there is a new record in the server section of hetzner."""
from telegram.ext import run_async
from telegram.ext import (
    CommandHandler,
    Updater,
)

from hetznerbot.config import config
from hetznerbot.models import Subscriber
from hetznerbot.helper import (
    help_text,
    session_wrapper,
    get_subscriber_info,
)
from hetznerbot.helper.hetzner import (
    send_offers,
    update_offers,
    get_hetzner_offers,
    check_offers_for_subscribers,
    check_all_offers_for_subscriber,
)


@run_async
def send_help_text(bot, update):
    """Send a help text."""
    bot.sendMessage(chat_id=update.message.chat_id, text=help_text)


@run_async
@session_wrapper()
def info(bot, update, session):
    """Get the newest hetzner offers."""
    chat_id = update.message.chat_id
    subscriber = Subscriber.get_or_create(session, chat_id)

    bot.sendMessage(chat_id=chat_id, text=get_subscriber_info(subscriber))


@session_wrapper()
def get_offers(bot, update, session):
    """Get the newest hetzner offers."""
    subscriber = Subscriber.get_or_create(session, update.message.chat_id)

    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session, get_all=True)


@run_async
@session_wrapper()
def set_parameter(bot, update, session):
    """Set query attributes."""
    chat_id = update.message.chat_id
    subscriber = Subscriber.get_or_create(session, chat_id)

    text = update.message.text
    parameters = text.split(' ')[1:]

    parameter_names = ['hdd_count', 'hdd_size', 'raid', 'after_raid',
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
        elif value == 'raid5' == subscriber.hdd_count < 3 \
                or value == 'raid6' == subscriber.hdd_count < 4:
            bot.sendMessage(chat_id=chat_id,
                            text='Invalid raid type for current hdd_count. RAID5 needs at least 3 drives, RAID6 needs at least 4 drives')
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

    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session)


@run_async
@session_wrapper()
def start(bot, update, session):
    """Start the bot."""
    chat_id = update.message.chat_id

    subscriber = Subscriber.get_or_create(session, chat_id)
    subscriber.active = True
    session.add(subscriber)
    session.commit()

    bot.sendMessage(chat_id=update.message.chat_id, text=help_text)
    text = 'You will now receive offers. Type /help for more info.'
    bot.sendMessage(chat_id=chat_id, text=text)

    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session)


@run_async
@session_wrapper()
def stop(bot, update, session):
    """Stop the bot."""
    chat_id = update.message.chat_id

    subscriber = Subscriber.get_or_create(session, chat_id)
    subscriber.active = False
    session.add(subscriber)
    session.commit()

    text = "You won't receive any more offers."
    bot.sendMessage(chat_id=chat_id, text=text)


@session_wrapper(send_message=False)
def process_all(bot, job, session):
    """Check for every subscriber."""
    # Get hetzner offers. Early return if it doesn't work
    incoming_offers = get_hetzner_offers()
    if incoming_offers is None:
        return

    offers = update_offers(session, incoming_offers)
    check_offers_for_subscribers(session, offers)

    subscribers = session.query(Subscriber) \
        .filter(Subscriber.active.is_(True)) \
        .all()
    for subscriber in subscribers:
        send_offers(bot, subscriber, session)


# Initialize telegram updater and dispatcher
updater = Updater(token=config.TELEGRAM_API_KEY)
dispatcher = updater.dispatcher

# Create jobs
job_queue = updater.job_queue
job_queue.run_repeating(process_all, interval=120, first=0, name='Process all')

# Create handler
help_handler = CommandHandler('help', send_help_text)
get_handler = CommandHandler('get', get_offers)
set_handler = CommandHandler('set', set_parameter)
info_handler = CommandHandler('info', info)
stop_handler = CommandHandler('stop', stop)
start_handler = CommandHandler('start', start)

# Add handler
dispatcher.add_handler(help_handler)
dispatcher.add_handler(info_handler)
dispatcher.add_handler(get_handler)
dispatcher.add_handler(set_handler)
dispatcher.add_handler(stop_handler)
dispatcher.add_handler(start_handler)
