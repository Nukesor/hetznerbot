default: run

run:
    poetry run python main.py run

initdb *args:
    poetry run python main.py initdb {{ args }}
    poetry run alembic --config migrations/alembic.ini stamp head

migrate:
    poetry run alembic --config migrations/alembic.ini upgrade head

setup:
    poetry install

lint:
    poetry run black --check hetznerbot
    poetry run isort --check-only hetznerbot
    poetry run flake8 hetznerbot

format:
    # remove unused imports
    poetry run autoflake \
        --remove-all-unused-imports \
        --recursive \
        --in-place hetznerbot
    poetry run black hetznerbot
    poetry run isort hetznerbot


# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
