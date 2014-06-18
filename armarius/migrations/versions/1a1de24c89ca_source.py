"""source

Revision ID: 1a1de24c89ca
Revises: 12e64a32d52b
Create Date: 2014-06-18 11:51:51.773534

"""

# revision identifiers, used by Alembic.
revision = '1a1de24c89ca'
down_revision = '12e64a32d52b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('page', sa.Column('source', sa.Text(), nullable=True))
    op.add_column('page', sa.Column('source_type', sa.Enum('markdown', 'html'),
                  server_default='html', nullable=True))


def downgrade():
    op.drop_column('page', 'source_type')
    op.drop_column('page', 'source')
