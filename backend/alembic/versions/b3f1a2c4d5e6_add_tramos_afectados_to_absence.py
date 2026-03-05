"""add tramos_afectados to absence

Revision ID: b3f1a2c4d5e6
Revises: ca52feb773e9
Create Date: 2026-03-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b3f1a2c4d5e6'
down_revision: Union[str, None] = 'ca52feb773e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'absences',
        sa.Column('tramos_afectados', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('absences', 'tramos_afectados')
