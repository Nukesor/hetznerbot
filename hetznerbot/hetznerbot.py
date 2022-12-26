"""A bot which checks if there is a new record in the server section of hetzner."""
from telegram.ext import CommandHandler, Updater

from hetznerbot.commands import (
    get_offers,
    info,
    send_help_text,
    set_parameter,
    start,
    stop,
)
from hetznerbot.config import config
from hetznerbot.jobs import process_all


def init_app():
    """Build the telegram updater.

    This function registers all update handlers on the updater.
    It furthermore registers jobs background in the apscheduler library.
    """

    # Initialize telegram updater and dispatcher
    updater = Updater(
        token=config["telegram"]["api_key"],
        workers=config["telegram"]["worker_count"],
        use_context=True,
    )
    dispatcher = updater.dispatcher

    # Create jobs
    job_queue = updater.job_queue
    job_queue.run_repeating(process_all, interval=120, first=5, name="Process all")

    # Create handler
    help_handler = CommandHandler("help", send_help_text, run_async=True)
    get_handler = CommandHandler("get", get_offers, run_async=True)
    set_handler = CommandHandler("set", set_parameter, run_async=True)
    info_handler = CommandHandler("info", info, run_async=True)
    stop_handler = CommandHandler("stop", stop, run_async=True)
    start_handler = CommandHandler("start", start, run_async=True)

    # Add handler
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(info_handler)
    dispatcher.add_handler(get_handler)
    dispatcher.add_handler(set_handler)
    dispatcher.add_handler(stop_handler)
    dispatcher.add_handler(start_handler)

    return updater
