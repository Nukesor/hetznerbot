#!/bin/env python

from hetzner.hetznerbot import Hetzner

bot = Hetzner()
offers = bot.get_hetzner_offers()
formatted = bot.format_offers(offers)
print(formatted)
