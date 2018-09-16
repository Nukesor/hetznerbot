"""Config values for hetznerbot."""


class Config:
    """Config class for convenient configuration."""

    # Get your telegram api-key from @botfather
    TELEGRAM_API_KEY = None
    SQL_URI = 'sqlite:///hetznerbot.db'
    SENTRY_TOKEN = None


config = Config()
