"""empty message

Revision ID: 922f78ec3698
Revises: 001eedbc2f9a
Create Date: 2021-10-21 20:53:12.360366

"""

# revision identifiers, used by Alembic.
revision = '922f78ec3698'
down_revision = '001eedbc2f9a'

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

import app
import app.extensions



def upgrade():
    """
    Upgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mission',
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.Column('viewed', sa.DateTime(), nullable=False),
    sa.Column('guid', app.extensions.GUID(), nullable=False),
    sa.Column('title', sa.String(length=50), nullable=False),
    sa.Column('owner_guid', app.extensions.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['owner_guid'], ['user.guid'], name=op.f('fk_mission_owner_guid_user')),
    sa.PrimaryKeyConstraint('guid', name=op.f('pk_mission'))
    )
    with op.batch_alter_table('mission', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_mission_created'), ['created'], unique=False)
        batch_op.create_index(batch_op.f('ix_mission_owner_guid'), ['owner_guid'], unique=False)
        batch_op.create_index(batch_op.f('ix_mission_updated'), ['updated'], unique=False)

    op.create_table('mission_user_membership_enrollment',
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.Column('viewed', sa.DateTime(), nullable=False),
    sa.Column('mission_guid', app.extensions.GUID(), nullable=False),
    sa.Column('user_guid', app.extensions.GUID(), nullable=False),
    sa.ForeignKeyConstraint(['mission_guid'], ['mission.guid'], name=op.f('fk_mission_user_membership_enrollment_mission_guid_mission')),
    sa.ForeignKeyConstraint(['user_guid'], ['user.guid'], name=op.f('fk_mission_user_membership_enrollment_user_guid_user')),
    sa.PrimaryKeyConstraint('mission_guid', 'user_guid', name=op.f('pk_mission_user_membership_enrollment'))
    )
    with op.batch_alter_table('mission_user_membership_enrollment', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_mission_user_membership_enrollment_created'), ['created'], unique=False)
        batch_op.create_index(batch_op.f('ix_mission_user_membership_enrollment_updated'), ['updated'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    """
    Downgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mission_user_membership_enrollment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mission_user_membership_enrollment_updated'))
        batch_op.drop_index(batch_op.f('ix_mission_user_membership_enrollment_created'))

    op.drop_table('mission_user_membership_enrollment')
    with op.batch_alter_table('mission', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mission_updated'))
        batch_op.drop_index(batch_op.f('ix_mission_owner_guid'))
        batch_op.drop_index(batch_op.f('ix_mission_created'))

    op.drop_table('mission')
    # ### end Alembic commands ###
