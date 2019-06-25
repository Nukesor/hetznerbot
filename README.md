# Hetzner-Bot

A handy telegram bot which texts you as soon as there is a viable offer available on the hetzner server market.
It is possible to set several search parameter which need to be satisfied for an offer to be sent to you.

<p align="center">
    <img src="https://raw.githubusercontent.com/Nukesor/images/master/hetzner_bot_reply.png">
</p>

If the price of an offer is reduced you will get a new notification with the updated price.

Available commands:

        /start Start the bot
        /stop Stop the bot
        /set Set search attributes with this syntax: "\set hdd_count 3"
            Attributes are:
                - `hdd_count`    int (min number of hard drives)
                - `hdd_size`     int (min amount of GB for each disk)
                - `raid`        enum ('raid5', 'raid6', 'None')
                - `after_raid`  int (min size of raid after assembly in TB)
                - `cpu_rating`  int (min cpu rating)
                - `ram`         int (min RAM size in GB)
                - `price`       int (max Price in Euro)
                - `ecc`         bool (0 or 1)
                - `inic`        bool (0 or 1)
                - `hwr`         bool (0 or 1)
        /get Check hetzner now!
        /info Show the current search attributes.
        /help Show this text

Feel free to host your own or to use mine: @hetzner_offer_bot


## Installation and starting:
**This bot is developed for Linux.**

Windows isn't tested, but it shouldn't be too hard to make it compatible. Feel free to create a PR.

Dependencies: 
- `poetry` to manage and install dependencies.
- Hetznerbot uses sqlite by default

1. Clone the repository: 

        % git clone git@github.com:nukesor/hetznerbot && cd hetznerbot

2. Execute following commands to install all dependencies and to initialize the database:

        % poetry install
        % poetry run initdb.py

3. Either start hetznerbot once or copy the `hetznerbot.toml` manually to `~/.config/hetznerbot.toml` and adjust all necessary values.
4. Start the bot: `poetry run main.py`
