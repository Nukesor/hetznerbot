"""Uniq offer-subscriber

Revision ID: 2fdb5eeeecf1
Revises: 
Create Date: 2020-04-28 15:53:27.272358

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker


# revision identifiers, used by Alembic.
revision = "2fdb5eeeecf1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Session = sessionmaker()
    bind = op.get_bind()
    session = Session(bind=bind)

    session.execute('DELETE FROM offer_subscriber where subscriber_id is NULL')
    session.execute('UPDATE subscriber SET active = False')

    op.alter_column(
        "offer_subscriber", "offer_id", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column(
        "offer_subscriber", "subscriber_id", existing_type=sa.BIGINT(), nullable=False
    )
    op.create_unique_constraint(
        "uniq_offer_subscriber", "offer_subscriber", ["offer_id", "subscriber_id"]
    )
    op.add_column(
        "subscriber",
        sa.Column("authorized", sa.Boolean(), server_default="FALSE", nullable=False),
    )


def downgrade():
    op.drop_column("subscriber", "authorized")
    op.drop_constraint("uniq_offer_subscriber", "offer_subscriber", type_="unique")
    op.alter_column(
        "offer_subscriber", "subscriber_id", existing_type=sa.BIGINT(), nullable=True
    )
    op.alter_column(
        "offer_subscriber", "offer_id", existing_type=sa.INTEGER(), nullable=True
    )
