# Hetzner-Bot

[![MIT Licence](https://img.shields.io/badge/license-MIT-success.svg)](https://github.com/Nukesor/pollbot/blob/master/LICENSE.md)

A handy telegram bot which texts you as soon as there is a viable offer available on the hetzner server market.
It is possible to set several search parameter which need to be satisfied for an offer to be sent to you.

<p align="center">
    <img src="https://raw.githubusercontent.com/Nukesor/images/master/hetzner_bot_reply.png">
</p>

If the price of an offer is reduced you will get a new notification with the updated price.

Available commands:

```txt
/start Start the bot
/stop Stop the bot
/set Set search attributes with this syntax: "\set hdd_count 3"
    Attributes are:
        - `hdd_count`    int (min number of hard drives)
        - `hdd_size`     int (min amount of GB for each disk)
        - `raid`        enum ('raid5', 'raid6', 'None')
        - `after_raid`  int (min size of raid after assembly in TB)
        - `ram`         int (min RAM size in GB)
        - `price`       int (max Price in Euro)
        - `ecc`         bool (0 or 1)
        - `inic`        bool (0 or 1)
        - `hwr`         bool (0 or 1)
/get Check hetzner now!
/info Show the current search attributes.
/help Show this text
```

Feel free to host your own or to use mine: @hetzner_offer_bot

## Installation and run

**This bot is developed for Linux.**

Windows isn't tested, but it shouldn't be too hard to make it compatible. Feel free to create a PR.

Dependencies:

- `poetry` to manage and install dependencies.
- [Just](https://github.com/casey/just) for convience.
- Hetznerbot uses postgres by default

1. Clone the repository:

    ```sh
    git clone git@github.com:nukesor/hetznerbot && cd hetznerbot
    ```
1. Run `just setup` to install dependencies
1. Run `just initdb` to initialize the database
1. Start the bot once with `just run` to create the default config at `~/.config/hetznerbot.toml`
1. Adjust the config file
1. Start the bot with `just run`

## Bot Commands

```txt
start - Start the bot
stop - Stop the bot
get - Get the newest Offers
info - Show the current search attributes
help - Show the help text
```
