"""Session helper."""
import traceback
from functools import wraps

from hetznerbot.config import config
from hetznerbot.db import get_session
from hetznerbot.models import Subscriber
from hetznerbot.sentry import sentry


def job_session_wrapper(func):
    """Create a session and handle exceptions for jobs."""

    async def wrapper(context):
        session = get_session()
        try:
            await func(context, session)

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
        async def wrapper(update, context):
            session = get_session()
            try:
                chat_id = update.message.chat_id
                username = update.message.from_user.username
                if username is not None:
                    username = username.lower()

                subscriber = Subscriber.get_or_create(session, chat_id)

                if (
                    not subscriber.authorized
                    and subscriber.chat_id != config["telegram"]["admin_id"]
                    and (username != config["telegram"]["admin"])
                ):
                    print("{}".format(config["telegram"]["admin_id"]))
                    await update.message.chat.send_message(
                        "Sorry. Hetznerbot is no longer public."
                    )
                    return

                await func(context.bot, update, session, subscriber)
                session.commit()
            except:  # noqa E722
                if send_message:
                    await context.bot.sendMessage(
                        chat_id=update.message.chat_id,
                        text="An unknown error occurred.",
                    )
                traceback.print_exc()
                sentry.capture_exception(tags={"handler": "normal"})
            finally:
                session.remove()

        return wrapper

    return real_decorator
