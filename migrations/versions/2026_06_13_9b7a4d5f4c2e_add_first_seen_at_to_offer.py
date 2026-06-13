"""add first_seen_at to offer

Revision ID: 9b7a4d5f4c2e
Revises: 7760061bb98a
Create Date: 2026-06-13 11:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b7a4d5f4c2e"
down_revision = "7760061bb98a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "offer",
        sa.Column(
            "first_seen_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.execute("UPDATE offer SET first_seen_at = last_update")
    op.alter_column(
        "offer",
        "first_seen_at",
        nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade():
    op.drop_column("offer", "first_seen_at")
