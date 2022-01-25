# -*- coding: utf-8 -*-
"""empty message

Revision ID: fa952f537929
Revises: f2d512a7ccdd
Create Date: 2021-06-02 16:00:18.342313

"""
from alembic import op
import sqlalchemy as sa

import app
import app.extensions


# revision identifiers, used by Alembic.
revision = 'fa952f537929'
down_revision = 'f2d512a7ccdd'


def upgrade():
    """
    Upgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'annotation_keywords',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('viewed', sa.DateTime(), nullable=False),
        sa.Column('annotation_guid', app.extensions.GUID(), nullable=False),
        sa.Column('keyword_guid', app.extensions.GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['annotation_guid'],
            ['annotation.guid'],
            name=op.f('fk_annotation_keywords_annotation_guid_annotation'),
        ),
        sa.ForeignKeyConstraint(
            ['keyword_guid'],
            ['keyword.guid'],
            name=op.f('fk_annotation_keywords_keyword_guid_keyword'),
        ),
        sa.PrimaryKeyConstraint(
            'annotation_guid', 'keyword_guid', name=op.f('pk_annotation_keywords')
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    """
    Downgrade Semantic Description:
        ENTER DESCRIPTION HERE
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('annotation_keywords')
    # ### end Alembic commands ###
