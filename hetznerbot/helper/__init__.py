"""Some static stuff or helper functions for hetzner bot."""
import traceback
from functools import wraps

from hetznerbot.db import get_session
from hetznerbot.sentry import sentry


help_text = """A handy telegram bot which texts you as soon as there is a viable offer available on the hetzner server market.

It is possible to set several search parameter which need to be satisfied for an offer being sent to you.

If you encounter any bugs, please create an issue over here:
https://github.com/Nukesor/hetznerbot

Available commands:
/start Start the bot
/stop Stop the bot
/set Set attributes with this syntax: "\set hdd_count 3"
    Attributes are:
        - `hdd_count`    int (min number of hard drives)
        - `hdd_size`       int (min amount of GB for each disk)
        - `raid`             enum ('raid5', 'raid6', 'None')
        - `after_raid`   int (min size of raid after assembly in GB)
        - `cpu_rating`  int (min cpu rating)
        - `ram`              int (min RAM size in GB)
        - `inic [0,1]`  bool (1 if the offer has to have an iNIC)
        - `ecc [0,1]`     bool (1 if the offer has to have ECC RAM)
        - `hwr [0,1]`     bool (1 if the offer has to have a HWR)
        - `price`            int (max Price in Euro)
/get Check hetzner now!
/info Show the current search attributes.
/help Show this text
"""


def get_subscriber_info(subscriber):
    """Return the formatted information about the current subscriber."""
    return """hdd_count: {0}
hdd_size: {1} GB
raid: {2}
after_raid: {3} GB
cpu_rating: {4}
ecc: {5}
inic: {6}
hwr: {7}
ram: {8} GB
price: {9} Euro""".format(
            subscriber.hdd_count,
            subscriber.hdd_size,
            subscriber.raid,
            subscriber.after_raid,
            subscriber.cpu_rating,
            subscriber.ecc,
            subscriber.inic,
            subscriber.hwr,
            subscriber.ram,
            subscriber.price,
        )


def job_session_wrapper():
    """Create a session and handle exceptions for jobs."""
    def real_decorator(func):
        """Parametrized decorator closure."""
        @wraps(func)
        def wrapper(context):
            session = get_session()
            try:
                func(context, session)

                session.commit()
            except: # noqa
                traceback.print_exc()
                sentry.captureException()
            finally:
                session.close()
        return wrapper

    return real_decorator


def session_wrapper(send_message=True):
    """Allow specification whether a debug message should be sent to the user."""
    def real_decorator(func):
        """Create a database session and handle exceptions."""
        @wraps(func)
        def wrapper(bot, update):
            session = get_session()
            try:
                func(bot, update, session)
                session.commit()
            except:
                if send_message:
                    bot.sendMessage(
                        chat_id=update.message.chat_id,
                        text='An unknown error occurred.',
                    )
                traceback.print_exc()
                sentry.captureException()
            finally:
                session.remove()
        return wrapper

    return real_decorator


def is_int_or_float(string):
    """Check if the string is an int or float."""
    try:
        int(string)
        return True
    except ValueError:
        try:
            float(string)
            return True
        except ValueError:
            pass
        pass

    return False


def int_or_float(string):
    """Return int or float."""
    try:
        x = int(string)
        return x
    except ValueError:
        x = float(string.replace(',', '.'))
        return x
