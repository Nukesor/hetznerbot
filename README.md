# Hetzner-Bot

A handy telegram bot which texts you as soon as there is a viable offer available on the hetzner server market.
It is possible to set several search parameter which need to be satisfied for an offer to be sent to you.

![Pueue](https://raw.githubusercontent.com/Nukesor/images/master/hetzner_bot_reply.png)

If the price of an offer is reduced you will get a new notification with the updated price.

Available commands:

        /start Start the bot
        /stop Start the bot
        /set Set search attributes with this syntax: "\set hd_count 3"
            Attributes are:
                - `hd_count`    int (Number of hard drives)
                - `hd_size`      int (Minimum for each disk in GB)
                - `raid`            enum ('raid5', 'raid6', 'None')
                - `after_raid`   int (Size after raid assembly in TB)
                - `cpu_rating`  int
                - `ram`             int (RAM size in GB)
                - `price`           int (Price in Euro)
        /get Check hetzner now!
        /info Get the current attributes.
        /help Show this text

Feel free to host your own or to use mine: @hetzner_offer_bot
