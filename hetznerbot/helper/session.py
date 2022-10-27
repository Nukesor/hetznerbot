"""Session helper."""
import traceback
from functools import wraps

from hetznerbot.config import config
from hetznerbot.db import get_session
from hetznerbot.models import Subscriber
from hetznerbot.sentry import sentry


def job_session_wrapper(func):
    """Create a session and handle exceptions for jobs."""

    def wrapper(context):
        session = get_session()
        try:
            func(context, session)

            session.commit()
        except:  # noqa
            traceback.print_exc()
            sentry.capture_exception(tags={"handler": "job"})
        finally:
            session.close()

    return wrapper


def session_wrapper(send_message=True):
    """Allow specification whether a debug message should be sent to the user."""

    def real_decorator(func):
        """Create a database session and handle exceptions."""

        @wraps(func)
        def wrapper(update, context):
            session = get_session()
            try:
                subscriber = Subscriber.get_or_create(session, update.message.chat_id)

                username = update.message.from_user.username
                if (
                    not subscriber.authorized
                    and username is not None
                    and username.lower() != config["telegram"]["admin"]
                ):
                    update.message.chat.send_message(
                        "Sorry. Hetznerbot is no longer public."
                    )
                    return

                func(context.bot, update, session, subscriber)
                session.commit()
            except:  # noqa E722
                if send_message:
                    context.bot.sendMessage(
                        chat_id=update.message.chat_id,
                        text="An unknown error occurred.",
                    )
                traceback.print_exc()
                sentry.capture_exception(tags={"handler": "normal"})
            finally:
                session.remove()

        return wrapper

    return real_decorator
