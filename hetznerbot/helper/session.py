"""Session helper."""
import traceback
from functools import wraps

from hetznerbot.db import get_session
from hetznerbot.sentry import sentry


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
            except:  # noqa
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
        def wrapper(update, context):
            session = get_session()
            try:
                func(context.bot, update, session)
                session.commit()
            except:
                if send_message:
                    context.bot.sendMessage(
                        chat_id=update.message.chat_id,
                        text="An unknown error occurred.",
                    )
                traceback.print_exc()
                sentry.captureException()
            finally:
                session.remove()

        return wrapper

    return real_decorator
