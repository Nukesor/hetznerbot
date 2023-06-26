"""A bot which checks if there is a new record in the server section of hetzner."""
from telegram.ext import Application, CommandHandler

from hetznerbot.commands import (
    authorize,
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

    # Initialize telegram updater and application
    app = (
        Application.builder()
        .token(config["telegram"]["api_key"])
        .concurrent_updates(config["telegram"]["worker_count"])
        .build()
    )

    # Create jobs
    job_queue = app.job_queue
    job_queue.run_repeating(process_all, interval=120, first=5, name="Process all")

    # Create handler
    help_handler = CommandHandler("help", send_help_text, block=False)
    get_handler = CommandHandler("get", get_offers, block=False)
    set_handler = CommandHandler("set", set_parameter, block=False)
    info_handler = CommandHandler("info", info, block=False)
    stop_handler = CommandHandler("stop", stop, block=False)
    start_handler = CommandHandler("start", start, block=False)
    authorize_handler = CommandHandler("authorize", authorize, block=False)

    # Add handler
    app.add_handler(help_handler)
    app.add_handler(info_handler)
    app.add_handler(get_handler)
    app.add_handler(set_handler)
    app.add_handler(stop_handler)
    app.add_handler(start_handler)
    app.add_handler(authorize_handler)

    return app
