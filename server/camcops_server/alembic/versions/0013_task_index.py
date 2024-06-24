"""
camcops_server/alembic/versions/0013_task_index.py

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

DATABASE REVISION SCRIPT

Task index

Revision ID: 0013
Revises: 0012
Creation date: 2018-11-10 22:54:18.529528

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa

from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "_idnum_index",
        sa.Column("idnum_pk", sa.Integer(), nullable=False),
        sa.Column("indexed_at_utc", sa.DateTime(), nullable=False),
        sa.Column("patient_pk", sa.Integer(), nullable=True),
        sa.Column("which_idnum", sa.Integer(), nullable=False),
        sa.Column("idnum_value", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["which_idnum"],
            ["_idnum_definitions.which_idnum"],
            name=op.f("fk__idnum_index_which_idnum"),
        ),
        sa.PrimaryKeyConstraint("idnum_pk", name=op.f("pk__idnum_index")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_idnum_index", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix__idnum_index_idnum_pk"), ["idnum_pk"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix__idnum_index_patient_pk"),
            ["patient_pk"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix__idnum_index_which_idnum"),
            ["which_idnum"],
            unique=False,
        )

    op.create_table(
        "_task_index",
        sa.Column(
            "index_entry_pk", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column("indexed_at_utc", sa.DateTime(), nullable=False),
        sa.Column("task_table_name", sa.String(length=128), nullable=True),
        sa.Column("task_pk", sa.Integer(), nullable=True),
        sa.Column("patient_pk", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("era", sa.String(length=32), nullable=False),
        sa.Column("when_created_utc", sa.DateTime(), nullable=False),
        sa.Column(
            "when_created_iso",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column("when_added_batch_utc", sa.DateTime(), nullable=False),
        sa.Column("adding_user_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("task_is_complete", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk__task_index_adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["_security_devices.id"],
            name=op.f("fk__task_index_device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["_security_groups.id"],
            name=op.f("fk__task_index_group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["patient_pk"],
            ["patient._pk"],
            name=op.f("fk__task_index_patient_pk"),
        ),
        sa.PrimaryKeyConstraint("index_entry_pk", name=op.f("pk__task_index")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("_task_index", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix__task_index_device_id"), ["device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_era"), ["era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_group_id"), ["group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_patient_pk"),
            ["patient_pk"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_task_pk"), ["task_pk"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_task_table_name"),
            ["task_table_name"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_when_created_iso"),
            ["when_created_iso"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix__task_index_when_created_utc"),
            ["when_created_utc"],
            unique=False,
        )

    # ### end Alembic commands ###


# noinspection PyPep8,PyTypeChecker
def downgrade():
    op.drop_table("_task_index")
    op.drop_table("_idnum_index")
