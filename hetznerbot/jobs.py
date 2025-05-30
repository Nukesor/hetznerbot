from sqlalchemy import select
from telegram.error import BadRequest, Forbidden

from hetznerbot.helper.hetzner import (
    check_offers_for_subscribers,
    get_hetzner_offers,
    notify_about_new_cpu,
    send_offers,
    update_offers,
)
from hetznerbot.helper.session import job_session_wrapper
from hetznerbot.models import Subscriber


@job_session_wrapper
async def process_all(context, session):
    """Check for every subscriber."""
    # Get hetzner offers. Early return if it doesn't work
    incoming_offers = get_hetzner_offers()
    if incoming_offers is None:
        print("Failed to receive Hetzner offers")
        return

    update_offers(session, incoming_offers)
    check_offers_for_subscribers(session)
    await notify_about_new_cpu(context, session)

    query = (
        select(Subscriber)
        .filter(Subscriber.authorized.is_(True))
        .filter(Subscriber.active.is_(True))
    )

    subscribers = session.scalars(query).all()
    for subscriber in subscribers:
        try:
            await send_offers(context.bot, subscriber, session)
        except BadRequest as e:
            if e.message == "Chat not found":
                session.delete(subscriber)
                session.commit()
        # Bot was removed from group
        except Forbidden:
            session.delete(subscriber)
            session.commit()
