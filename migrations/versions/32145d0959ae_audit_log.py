# -*- coding: utf-8 -*-
"""audit_log

Revision ID: 32145d0959ae
Revises: 2d3ba401d0f0
Create Date: 2021-09-01 14:41:25.158199

"""
from alembic import op
import sqlalchemy as sa

import app
import app.extensions


# revision identifiers, used by Alembic.
revision = '32145d0959ae'
down_revision = '2d3ba401d0f0'


def upgrade():
    """
    Upgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'audit_log',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('guid', app.extensions.GUID(), nullable=False),
        sa.Column('module_name', sa.String(length=50), nullable=True),
        sa.Column('item_guid', app.extensions.GUID(), nullable=True),
        sa.Column('user_email', sa.String(length=120), nullable=False),
        sa.Column('message', sa.String(length=240), nullable=True),
        sa.Column('audit_type', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('guid', name=op.f('pk_audit_log')),
    )
    # ### end Alembic commands ###


def downgrade():
    """
    Downgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('audit_log')
    # ### end Alembic commands ###
