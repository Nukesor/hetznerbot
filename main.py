#!/bin/env python
"""Start the bot."""

from hetznerbot.hetznerbot import updater

updater.start_polling()
updater.idle()
