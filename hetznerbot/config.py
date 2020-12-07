"""Config for hetznerbot."""
import os
import sys
import toml


default_config = {
    "telegram": {
        "api_key": "your_telegram_api_key",
        "worker_count": 5,
        "admin": "nukesor",
    },
    "database": {
        "sql_uri": "sqlite:///hetznerbot",
    },
    "logging": {
        "sentry_enabled": False,
        "sentry_token": "",
    },
    "webhook": {
        "enabled": False,
        "domain": "https://localhost",
        "token": "hetznerbot",
        "cert_path": "/path/to/cert.pem",
        "port": 7000,
    },
}

config_path = os.path.expanduser("~/.config/hetznerbot.toml")

if not os.path.exists(config_path):
    with open(config_path, "w") as file_descriptor:
        toml.dump(default_config, file_descriptor)
    print("Please adjust the configuration file at '~/.config/hetznerbot.toml'")
    sys.exit(1)
else:
    config = toml.load(config_path)
