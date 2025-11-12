default: run

run:
    uv run ./main.py run

initdb *args:
    uv run ./main.py initdb {{ args }}
    uv run alembic --config migrations/alembic.ini stamp head
    uv run ./main.py import-cpu-data

migrate:
    uv run alembic --config migrations/alembic.ini upgrade head

generate-migration *args:
    uv run alembic --config migrations/alembic.ini revision --autogenerate {{ args }}

setup:
    uv sync

lint:
    uv run ruff check ./hetznerbot --output-format=full
    uv run ruff format ./hetznerbot --diff
    taplo format --check

format:
    uv run ruff check --fix ./hetznerbot
    uv run ruff format ./hetznerbot
    taplo format

import_cpu_data:
    uv run ./main.py import-cpu-data

# Watch for something
# E.g. `just watch lint` or `just watch test`
watch *args:
    watchexec --clear 'just {{ args }}'
