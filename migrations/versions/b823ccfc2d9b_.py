# -*- coding: utf-8 -*-
"""empty message

Revision ID: b823ccfc2d9b
Revises: 2a02d5f72c3b
Create Date: 2021-08-10 05:37:19.652762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b823ccfc2d9b'
down_revision = '2a02d5f72c3b'


def upgrade():
    """
    Upgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('collaboration', schema=None) as batch_op:
        batch_op.drop_column('title')

    # ### end Alembic commands ###


def downgrade():
    """
    Downgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('collaboration', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('title', sa.VARCHAR(length=50), autoincrement=False, nullable=True)
        )

    # ### end Alembic commands ###
