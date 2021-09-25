from hetznerbot.helper import (
    help_text,
    get_subscriber_info,
)
from hetznerbot.helper.session import (
    session_wrapper,
)
from hetznerbot.helper.hetzner import (
    send_offers,
    check_all_offers_for_subscriber,
)


@session_wrapper()
def send_help_text(bot, update, session, subscriber):
    """Send a help text."""
    bot.send_message(chat_id=update.message.chat_id, text=help_text)


@session_wrapper()
def info(bot, update, session, subscriber):
    """Get the newest hetzner offers."""
    bot.send_message(
        chat_id=update.message.chat_id, text=get_subscriber_info(subscriber)
    )


@session_wrapper()
def get_offers(bot, update, session, subscriber):
    """Get the newest hetzner offers."""
    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session, get_all=True)


@session_wrapper()
def set_parameter(bot, update, session, subscriber):
    """Set query attributes."""
    chat = update.message.chat

    text = update.message.text
    parameters = text.split(" ")[1:]

    parameter_names = [
        "hdd_count",
        "hdd_size",
        "raid",
        "after_raid",
        "datacenter",
        "cpu_rating",
        "ram",
        "price",
        "ecc",
        "inic",
        "hwr",
    ]

    # We need exactly two parameter. Name and value
    if len(parameters) != 2:
        chat.send_message("Exactly two parameter need to be specified.")
        return

    [name, value] = parameters

    # Check if we know this parameter
    if name not in parameter_names:
        chat.send_message("Invalid parameter. Type /help for more information")
        return

    # validate raid choices
    if name == "raid":
        if value not in ["raid5", "raid6", "None"]:
            chat.send_message(
                'Invalid value for "raid". Type /help for more information'
            )
            return

        # Check if raid is possible with hdd_count
        if (
            value == "raid5" == subscriber.hdd_count < 3
            or value == "raid6" == subscriber.hdd_count < 4
        ):
            chat.send_message(
                "Invalid raid type for current hdd_count. RAID5 needs at least 3 drives, RAID6 needs at least 4 drives"
            )
            return

        # No raid
        if value == "None":
            value = None

    elif name == "datacenter":
        datacenters = ["NBG", "FSN", "HEL", "None"]
        if value not in datacenters:
            chat.send_message(
                f'Invalid value for "datacenter". Please send one of these: {datacenters}'
            )
            return

        # None value
        if value == "None":
            value = None

    # Validate int values
    else:
        try:
            value = int(value)
        except BaseException:
            chat.send_message("Value is not an int.")
            return

    # Validate boolean values
    if name in ["ecc", "inic", "hwr"]:
        if value not in [0, 1]:
            chat.send_message("The value needs to be a boolean (0 or 1)")
            return

        value = bool(value)

    setattr(subscriber, name, value)
    session.add(subscriber)
    session.commit()

    chat.send_message(f"*{name}* changed to {value}", parse_mode="Markdown")

    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session)


@session_wrapper()
def start(bot, update, session, subscriber):
    """Start the bot."""
    subscriber.active = True
    session.add(subscriber)
    session.commit()

    bot.send_message(chat_id=update.message.chat_id, text=help_text)
    text = "You will now receive offers. Type /help for more info."
    bot.send_message(chat_id=update.message.chat_id, text=text)

    check_all_offers_for_subscriber(session, subscriber)
    send_offers(bot, subscriber, session)


@session_wrapper()
def stop(bot, update, session, subscriber):
    """Stop the bot."""
    subscriber.active = False
    session.add(subscriber)
    session.commit()

    text = "You won't receive any more offers."
    bot.send_message(chat_id=update.message.chat_id, text=text)
