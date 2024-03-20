default: run

run:
    poetry run python main.py run

initdb *args:
    poetry run python main.py initdb {{ args }}
    poetry run alembic --config migrations/alembic.ini stamp head

migrate:
    poetry run alembic --config migrations/alembic.ini upgrade head

generate-migration *args:
    poetry run alembic --config migrations/alembic.ini revision --autogenerate {{ args }}

setup:
    poetry install

lint:
    poetry run ruff check ./hetznerbot --output-format=full
    poetry run ruff format ./hetznerbot --diff

format:
    poetry run ruff check --fix ./hetznerbot
    poetry run ruff format ./hetznerbot

import_cpu_data:
    poetry run python ./main.py import-cpu-data

# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
