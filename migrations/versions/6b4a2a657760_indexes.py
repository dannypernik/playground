"""indexes

Revision ID: 6b4a2a657760
Revises: 4780158ba4af
Create Date: 2021-09-16 23:18:16.581206

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b4a2a657760'
down_revision = '4780158ba4af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_student_email'), ['student_email'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_student_name'), ['student_name'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_student_student_name'))
        batch_op.drop_index(batch_op.f('ix_student_student_email'))
        batch_op.drop_index(batch_op.f('ix_student_active'))

    # ### end Alembic commands ###
