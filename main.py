#!/bin/env python
"""Start the bot."""

from hetzner.hetznerbot import updater

updater.start_polling()
updater.idle()
