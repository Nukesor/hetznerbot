"""Some static stuff or helper functions for hetzner bot."""


attributes = [
    'cpu',
    'cpu_rating',
    'ram',
    'hd',
    'price',
    'next_reduction',
]

help_text = """A nice little telegram bot, which texts you,
if there are any offers on the hetzner server market,
that match your defined criteria.

If you encounter any bugs, create an issue over here:
https://github.com/Nukesor/hetznerbot

Available commands:
/start Start the bot
/stop Start the bot
/set Set attributes with this syntax: "\set hd_count 3"
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
