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
        /get Check hetzner now!
        /info Show the current search attributes.
        /help Show this text

Feel free to host your own or to use mine: @hetzner_offer_bot


## Installation and starting:

Clone the repository: 

    % git clone git@github.com:nukesor/hetznerbot && cd hetzner

Now copy the `hetzner/config.example.py` to `hetzner/config.py` and adjust all necessary values.
Finally execute following commands to install all dependencies and to start the bot:

    % make
    % source ./venv/bin/activate
    % ./initdb.py
    % ./main.py

