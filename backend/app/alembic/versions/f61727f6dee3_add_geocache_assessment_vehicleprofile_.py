"""add geocache assessment vehicleprofile tables

Revision ID: f61727f6dee3
Revises: fe56fa70289e
Create Date: 2026-02-13 18:33:30.024185

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = 'f61727f6dee3'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('geocache',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('cache_key', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('data_json', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_geocache_cache_key'), 'geocache', ['cache_key'], unique=True)
    op.create_table('vehicleprofile',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('vehicle_class', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('width_m', sa.Float(), nullable=False),
    sa.Column('length_m', sa.Float(), nullable=False),
    sa.Column('height_m', sa.Float(), nullable=False),
    sa.Column('weight_kg', sa.Integer(), nullable=False),
    sa.Column('turning_radius_m', sa.Float(), nullable=False),
    sa.Column('mirror_width_m', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assessment',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('postcode', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('easting', sa.Float(), nullable=False),
    sa.Column('northing', sa.Float(), nullable=False),
    sa.Column('results_json', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('overall_rating', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_postcode'), 'assessment', ['postcode'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_assessment_postcode'), table_name='assessment')
    op.drop_table('assessment')
    op.drop_table('vehicleprofile')
    op.drop_index(op.f('ix_geocache_cache_key'), table_name='geocache')
    op.drop_table('geocache')
