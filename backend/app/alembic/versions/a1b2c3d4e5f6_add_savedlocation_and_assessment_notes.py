"""add savedlocation table and assessment notes column

Revision ID: a1b2c3d4e5f6
Revises: f61727f6dee3
Create Date: 2026-02-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f61727f6dee3'
branch_labels = None
depends_on = None


def upgrade():
    # Add notes column to assessment table
    op.add_column('assessment', sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=True))

    # Create savedlocation table
    op.create_table('savedlocation',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('label', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column('postcode', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_savedlocation_postcode'), 'savedlocation', ['postcode'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_savedlocation_postcode'), table_name='savedlocation')
    op.drop_table('savedlocation')
    op.drop_column('assessment', 'notes')
