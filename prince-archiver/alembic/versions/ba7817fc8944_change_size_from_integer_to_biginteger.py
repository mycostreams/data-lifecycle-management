"""Change size from Integer to BigInteger

Revision ID: ba7817fc8944
Revises: d25b5aa9841d
Create Date: 2024-11-26 13:37:41.288854

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ba7817fc8944"
down_revision: Union[str, None] = "d25b5aa9841d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "event_archives",
        "size",
        existing_type=sa.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )
    op.alter_column(
        "imaging_events",
        "system",
        existing_type=sa.VARCHAR(length=6),
        type_=sa.Enum(
            "PRINCE",
            "TSU_EXP002",
            "TSU_EXP003",
            name="system",
            native_enum=False,
        ),
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "imaging_events",
        "system",
        existing_type=sa.Enum(
            "PRINCE",
            "TSU_EXP002",
            "TSU_EXP003",
            name="system",
            native_enum=False,
        ),
        type_=sa.VARCHAR(length=6),
        existing_nullable=True,
    )
    op.alter_column(
        "event_archives",
        "size",
        existing_type=sa.BigInteger(),
        type_=sa.INTEGER(),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
