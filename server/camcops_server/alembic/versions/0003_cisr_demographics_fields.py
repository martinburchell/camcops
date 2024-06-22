"""
camcops_server/alembic/versions/0003_cisr_demographics_fields.py

===============================================================================

    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.

===============================================================================

CISR demographics fields 2018-02-02
Revision ID: 0003
Revises: 0002
Creation date: 2018-02-02 10:02:46.382218
DATABASE REVISION SCRIPT
"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("cisr", schema=None) as batch_op:
        batch_op.add_column(sa.Column("empstat", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("emptype", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("ethnic", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("home", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("married", sa.Integer(), nullable=True))

    # ### end Alembic commands ###


# noinspection PyPep8
def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("cisr", schema=None) as batch_op:
        batch_op.drop_column("married")
        batch_op.drop_column("home")
        batch_op.drop_column("ethnic")
        batch_op.drop_column("emptype")
        batch_op.drop_column("empstat")

    # ### end Alembic commands ###
