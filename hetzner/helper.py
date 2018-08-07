"""Some static stuff or helper functions for hetzner bot."""


attributes = [
    'cpu',
    'cpu_rating',
    'ram',
    'hd',
    'price',
    'next_reduction',
]

help_text = """A handy telegram bot which texts you as soon as there is a viable offer available on the hetzner server market.

It is possible to set several search parameter which need to be satisfied for an offer to be sent to you.

If you encounter any bugs, please create an issue over here:
https://github.com/Nukesor/hetznerbot

Available commands:
/start Start the bot
/stop Start the bot
/set Set attributes with this syntax: "\set hd_count 3"
    Attributes are:
        - `hd_count`    int (min number of hard drives)
        - `hd_size`       int (min amount of GB for each disk)
        - `raid`             enum ('raid5', 'raid6', 'None')
        - `after_raid`   int (min size of raid after assembly in TB)
        - `cpu_rating`  int (min cpu rating)
        - `ram`              int (min RAM size in GB)
        - `price`            int (max Price in Euro)
/get Check hetzner now!
/info Show the current search attributes.
/help Show this text
"""


def is_int_or_float(string):
    """Check if the string is an int or float."""
    try:
        int(string)
        return True
    except ValueError:
        try:
            float(string)
            return True
        except ValueError:
            pass
        pass

    return False


def int_or_float(string):
    """Return int or float."""
    try:
        x = int(string)
        return x
    except ValueError:
        x = float(string)
        return x
