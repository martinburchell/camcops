"""
camcops_server/alembic/versions/0005_reduced_indexed_varchar_fields_from_255.py

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

reduced indexed VARCHAR fields from 255 to 191 for MySQL
Revision ID: 0005
Revises: 0004
Creation date: 2018-09-24 16:25:45.525788
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

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # Altered 2018-11-09 to drop index before altering field, and recreate
    # index afterwards; otherwise SQL Server gives the error: "The index '...'
    # is dependent on column '...'."

    with op.batch_alter_table(
        "_security_account_lockouts", schema=None
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix__security_account_lockouts_username")
        )
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=255),
            type_=sa.String(length=191),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_account_lockouts_username"),
            ["username"],
            unique=False,
        )

    with op.batch_alter_table("_security_devices", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_devices_name"))
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=255),
            type_=sa.String(length=191),
            existing_nullable=True,
        )
        batch_op.create_index(
            batch_op.f("ix__security_devices_name"), ["name"], unique=True
        )

    with op.batch_alter_table("_security_groups", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_groups_name"))
        batch_op.alter_column(
            "name",
            existing_type=sa.Unicode(length=255),
            type_=sa.Unicode(length=191),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_groups_name"), ["name"], unique=True
        )

    with op.batch_alter_table(
        "_security_login_failures", schema=None
    ) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_login_failures_username"))
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=255),
            type_=sa.String(length=191),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_login_failures_username"),
            ["username"],
            unique=False,
        )

    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_users_username"))
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=255),
            type_=sa.String(length=191),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_users_username"),
            ["username"],
            unique=True,
        )

    # ### end Alembic commands ###


# noinspection PyPep8
def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # Altered 2018-11-09 as above.

    with op.batch_alter_table("_security_users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_users_username"))
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=191),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_users_username"),
            ["username"],
            unique=True,
        )

    with op.batch_alter_table(
        "_security_login_failures", schema=None
    ) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_login_failures_username"))
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=191),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_login_failures_username"),
            ["username"],
            unique=False,
        )

    with op.batch_alter_table("_security_groups", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_groups_name"))
        batch_op.alter_column(
            "name",
            existing_type=sa.Unicode(length=191),
            type_=sa.Unicode(length=255),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_groups_name"), ["name"], unique=True
        )

    with op.batch_alter_table("_security_devices", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix__security_devices_name"))
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=191),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
        batch_op.create_index(
            batch_op.f("ix__security_devices_name"), ["name"], unique=True
        )

    with op.batch_alter_table(
        "_security_account_lockouts", schema=None
    ) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix__security_account_lockouts_username")
        )
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=191),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix__security_account_lockouts_username"),
            ["username"],
            unique=False,
        )

    # ### end Alembic commands ###
