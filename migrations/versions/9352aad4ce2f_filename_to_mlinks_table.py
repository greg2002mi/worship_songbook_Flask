"""filename to mlinks table

Revision ID: 9352aad4ce2f
Revises: d8e2fc49a3e8
Create Date: 2023-05-31 15:21:21.233046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9352aad4ce2f'
down_revision = 'd8e2fc49a3e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mlinks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filename', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_mlinks_filename'), ['filename'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mlinks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mlinks_filename'))
        batch_op.drop_column('filename')

    # ### end Alembic commands ###