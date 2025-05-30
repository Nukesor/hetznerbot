"""Hetzner helper functions."""

import json
from datetime import datetime
from json import JSONDecodeError

import telegram
from requests import request
from requests.exceptions import ConnectionError
from sqlalchemy import select, update
from sqlalchemy.sql.selectable import and_

from hetznerbot.config import config
from hetznerbot.helper.disk_type import DiskType
from hetznerbot.helper.text import split_text
from hetznerbot.models import Cpu, Offer, OfferDisk, OfferSubscriber, Subscriber
from hetznerbot.sentry import sentry


def get_hetzner_offers():
    """Get the newest hetzner offers."""
    headers = {
        "Content-Type": "application/json, text/plain, */*",
        "Referer": "https://www.hetzner.de/sb",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            + " (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"
        ),
    }

    url = "https://www.hetzner.com/_resources/app/data/app/live_data_sb_EUR.json"
    try:
        response = request("GET", url, headers=headers)
        data = json.loads(response.content)
        return data["server"]
    except ConnectionError:
        print("Connection error while retrieving data.")
        return None
    except JSONDecodeError or UnicodeDecodeError:
        print("Failed to decode json.")
        sentry.capture_exception()
        return None


def populate_disk_data(
    offer_id: int, disks: list[OfferDisk], disk_type: DiskType, disk_size_entry: int
):
    """Set disk data and handle multiple disk types.

    Either increments the disk count of an existing member of `disks`
    or creates a new entry in it.
    """
    # skip general, it just repeats the info of other more specific categories.
    if disk_type == "general":
        return

    # go through every disk entry
    for disk in disks:
        # if there's already a disk in the list that matches the current
        # specifications, increment the count.
        if disk.type == disk_type and disk.size == disk_size_entry:
            disk.amount += 1
            return

    # if none of the existing disks matched, we create a new one.
    disks.append(OfferDisk(offer_id, disk_type, disk_size_entry))


def update_offers(session, incoming_offers):
    """Update all offers and check for updates."""
    active_ids = []
    offers = []

    for incoming_offer in incoming_offers:
        active_ids.append(incoming_offer["key"])
        offer = session.get(Offer, incoming_offer["key"])

        if not offer:
            offer = Offer(incoming_offer["key"])
            session.add(offer)

        offer.cpu = incoming_offer["cpu"].strip()
        offer.ram = incoming_offer["ram_size"]
        offer.datacenter = incoming_offer["datacenter"]

        # Generate disk data
        new_disks = []
        for disk_type in incoming_offer["serverDiskData"]:
            # skip general, it just repeats the info of other more specific categories.
            if disk_type == "general":
                continue

            disk_array = incoming_offer["serverDiskData"][disk_type]
            for disk_size_entry in disk_array:
                populate_disk_data(offer.id, new_disks, disk_type, disk_size_entry)

        # Create two sets, representing the old disk pool and the new disk pool.
        old_disks_set = set(
            [
                f"{disks.type.name}-{disks.size}-{disks.amount}"
                for disks in offer.offer_disks
            ]
        )
        new_disks_set = set(
            [f"{disks.type}-{disks.size}-{disks.amount}" for disks in new_disks]
        )

        # Check if the set of disks changed. If that's the case, update the disks
        if old_disks_set != new_disks_set:
            # clear out existing disk data
            for offer_disk in offer.offer_disks:
                session.delete(offer_disk)
            offer.offer_disks.clear()

            # add new disks to the offer
            for disk in new_disks:
                offer.offer_disks.append(disk)

        # Check for specials on this offer.
        offer.ecc = incoming_offer["is_ecc"]
        offer.ipv4 = "IPv4" in incoming_offer["specials"]
        offer.inic = "iNIC" in incoming_offer["specials"]
        offer.hwr = "HWR" in incoming_offer["specials"]

        # Calculate the price in cents
        price = incoming_offer["price"] * 100
        if offer.ipv4:
            # Ipv4 is an extra 1.70€
            price += 170

        # Notify all subscribers about the price change
        if offer.price is not None and offer.price != price:
            offer.last_update = datetime.now()
            # Mark the offer as "not new"
            for subscription in offer.offer_subscriber:
                subscription.notified = False
                subscription.new = False

        offer.price = price

        offer.deactivated = False
        offers.append(offer)

    # Deactivate all old offers
    session.execute(
        update(Offer)
        .where(Offer.deactivated.is_(False))
        .where(Offer.id.notin_(active_ids))
        .values(deactivated=True),
    )

    session.commit()

    return offers


def check_all_offers_for_subscriber(session, subscriber):
    """Check all offers for a specific subscriber."""
    check_offer_for_subscriber(session, subscriber)


def check_offers_for_subscribers(session):
    """Check for each offer if any subscriber are interested in it."""
    query = (
        select(Subscriber)
        .filter(Subscriber.authorized.is_(True))
        .filter(Subscriber.active.is_(True))
    )

    subscribers = session.scalars(query).all()
    for subscriber in subscribers:
        check_offer_for_subscriber(session, subscriber)


def check_offer_for_subscriber(session, subscriber):
    """Check the offers for a specific subscriber."""
    query = (
        select(Offer)
        .filter(Offer.deactivated.is_(False))
        .filter(Offer.price <= subscriber.price * 100)
        .filter(Offer.ram >= subscriber.ram)
        .filter(
            Offer.offer_disks.any(
                and_(
                    OfferDisk.type == DiskType.hdd,
                    OfferDisk.size >= subscriber.hdd_size,
                    OfferDisk.amount >= subscriber.hdd_count,
                )
            )
        )
        .filter(
            Offer.cpu.in_(
                session.query(Cpu.name)
                .filter(Cpu.threads >= subscriber.threads)
                .filter(Cpu.release_date >= subscriber.release_date)
                .filter(Cpu.multi_thread_rating >= subscriber.multi_rating)
                .filter(Cpu.single_thread_rating >= subscriber.single_rating)
            )
        )
    )

    # Calculate after_raid
    if subscriber.raid == "raid5":
        query = query.filter(
            Offer.offer_disks.any(
                and_(
                    OfferDisk.type == DiskType.hdd,
                    (OfferDisk.amount - 1) * OfferDisk.size >= subscriber.after_raid,
                )
            )
        )
    elif subscriber.raid == "raid6":
        query = query.filter(
            Offer.offer_disks.any(
                and_(
                    OfferDisk.type == DiskType.hdd,
                    (OfferDisk.amount - 2) * OfferDisk.size >= subscriber.after_raid,
                )
            )
        )

    if subscriber.datacenter is not None:
        query = query.filter(Offer.datacenter.startswith(subscriber.datacenter))

    if subscriber.ipv4:
        query = query.filter(Offer.ipv4.is_(True))

    if subscriber.ecc:
        query = query.filter(Offer.ecc.is_(True))

    if subscriber.inic:
        query = query.filter(Offer.inic.is_(True))

    if subscriber.hwr:
        query = query.filter(Offer.hwr.is_(True))

    matching_offers = session.scalars(query).all()
    for offer in matching_offers:
        # Check if there's already a relation relation.
        exists = list(
            filter(lambda o: o.offer_id == offer.id, subscriber.offer_subscriber)
        )

        # If not, create a new OfferSubscriber entity.
        if len(exists) == 0:
            offer_subscriber = OfferSubscriber(offer.id, subscriber.chat_id)
            subscriber.offer_subscriber.append(offer_subscriber)

            session.add(offer_subscriber)
            session.commit()

    # Clean old entries
    for offer_subscriber in subscriber.offer_subscriber:
        if offer_subscriber.offer not in matching_offers:
            session.delete(offer_subscriber)

    session.commit()


async def notify_about_new_cpu(context, session):
    """Check for any cpu for which no stats are present. If so, let the admin know."""
    query = (
        select(Offer.cpu).distinct().filter(Offer.cpu.notin_(session.query(Cpu.name)))
    )
    new_cpus = session.scalars(query).all()

    # Remove all cpus from the list for which we've already been notified
    if "new_cpus" not in context.bot_data:
        context.bot_data["new_cpus"] = []
    new_cpus = [cpu for cpu in new_cpus if cpu not in context.bot_data["new_cpus"]]

    # Early return if there's nothing to do
    if len(new_cpus) == 0:
        return

    # Build notification message
    info = "Please add info about these cpus:\n"
    for cpu in new_cpus:
        info += f"'{cpu}'\n"
        context.bot_data["new_cpus"].append(cpu)

    await context.bot.sendMessage(
        chat_id=config["telegram"]["admin_id"],
        text=info,
    )


def format_offers(session, subscriber, offer_subscriber, get_all=False):
    """Format the found offers."""
    # Filter all offers, which aren't notified yet, if the user doesn't want all offers.
    if not get_all:
        offer_subscriber = list(filter(lambda o: not o.notified, offer_subscriber))

    if len(offer_subscriber) == 0:
        return []

    formatted_offers = []
    for _, offer_subscriber in enumerate(offer_subscriber):
        # The subscriber should only receive new offers
        offer_subscriber.notified = True
        offer = offer_subscriber.offer

        # Whether this is a new entry or a price reduction occured.
        if offer_subscriber.new:
            offer_status = "(New)"
        else:
            offer_status = "(Price reduction)"

        # Format extra features
        extra_features = ""
        if offer.ipv4:
            extra_features += "IPv4 "
        if offer.ecc:
            extra_features += "ECC "
        if offer.inic:
            extra_features += "iNIC "
        if offer.hwr:
            extra_features += "HWR "
        if extra_features == "":
            extra_features = "None"

        # Get info on disk sizes
        biggest_raid_5_pool = None
        biggest_raid_6_pool = None
        disk_info = ""
        for offer_disk in offer.offer_disks:
            disk_info += (
                f"\n    - {offer_disk.amount}x "
                + f"*{format_size(offer_disk.size)}* "
                + f"{get_disk_type_name(offer_disk.type)}"
            )
            if offer_disk.amount >= 3:
                raid_5_pool = offer_disk.size * (offer_disk.amount - 1)
                if not biggest_raid_5_pool or raid_5_pool > biggest_raid_5_pool:
                    biggest_raid_5_pool = raid_5_pool

            if offer_disk.amount >= 4:
                raid_6_pool = offer_disk.size * (offer_disk.amount - 2)
                if not biggest_raid_6_pool or raid_6_pool > biggest_raid_6_pool:
                    biggest_raid_6_pool = raid_6_pool

        # Calculate the price including VAT.
        price = offer.price / 100
        price_incl_vat = float(offer.price) * 1.19 / 100

        # First chunk of data
        updated_date = offer.last_update.strftime("%d.%m - %H:%M")
        formatted_offer = f"""*Offer {offer.id} {offer_status}:* [ {updated_date} ]"""

        # Add cpu info, if possible
        cpu = session.get(Cpu, offer.cpu)
        if cpu is None:
            formatted_offer += f"\n_Cpu:_ {offer.cpu}"
        else:
            formatted_offer += f"""\n_Cpu:_ {cpu.name} ({cpu.release_date})
    - *{cpu.threads}* threads
    - Multi: *{cpu.multi_thread_rating}*
    - Single: *{cpu.single_thread_rating}*"""

        # Add ram and disk info
        formatted_offer += f"""\n_Ram:_ *{offer.ram} GB*
_Disks:_{disk_info}"""

        # Add raid info, if desired
        if subscriber.raid == "raid5":
            pool_string = (
                f"{format_size(biggest_raid_5_pool)}" if biggest_raid_5_pool else "n/a"
            )
            formatted_offer += f"\n_Raid5 capacity:_ *{pool_string}*"
        elif subscriber.raid == "raid6":
            pool_string = (
                f"{format_size(biggest_raid_6_pool)}" if biggest_raid_6_pool else "n/a"
            )
            formatted_offer += f"\n_Raid6 capacity:_ *{pool_string}*"

        # Remaining chunk of data
        formatted_offer += f"""
_Extra features:_ *{extra_features}*
_Price:_ {price:.2f}€ (VAT incl.: {price_incl_vat:.2f})
_Datacenter:_ {offer.datacenter}
        """

        formatted_offers.append(formatted_offer)

    formatted_offers = split_text(formatted_offers, max_chunks=5)

    return formatted_offers


def get_disk_type_name(disk_type: DiskType) -> str:
    if disk_type == DiskType.hdd:
        return "HDD"
    elif disk_type == DiskType.sata:
        return "SSD (Sata)"
    elif disk_type == DiskType.nvme:
        return "SSD (NVMe)"


def format_size(disk_size: int) -> str:
    if disk_size < 1000:
        return f"{disk_size} GB"
    else:
        return f"{disk_size / 1000} TB"


async def send_offers(bot, subscriber, session, get_all=False):
    """Send the newest update to all subscribers."""
    # Extract message meta data
    if get_all:
        formatted_offers = format_offers(
            session, subscriber, subscriber.offer_subscriber, get_all=True
        )
    else:
        formatted_offers = format_offers(
            session, subscriber, subscriber.offer_subscriber
        )

    if len(formatted_offers) > 0:
        for chunk in formatted_offers:
            try:
                await bot.sendMessage(
                    chat_id=subscriber.chat_id,
                    text=chunk,
                    parse_mode="Markdown",
                )
            except telegram.error.Forbidden:
                session.delete(subscriber)
                session.commit()

        if formatted_offers == 5:
            await bot.sendMessage(
                chat_id=subscriber.chat_id,
                text="Too many results, please narrow down your search a little.",
            )
            return
    else:
        if get_all:
            await bot.sendMessage(
                chat_id=subscriber.chat_id,
                parse_mode="Markdown",
                text="There are currently no offers for your criteria.",
            )
