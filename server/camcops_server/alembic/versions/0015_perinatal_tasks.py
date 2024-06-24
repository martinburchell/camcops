"""
camcops_server/alembic/versions/0015_perinatal_tasks.py

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

perinatal tasks:

- apeqpt
- gbogres
- ors
- srs

Revision ID: 0015
Revises: 0014
Creation date: 2019-02-04 10:09:25.229002

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa

from camcops_server.cc_modules.cc_sqla_coltypes import (
    PendulumDateTimeAsIsoTextColType,
    SemanticVersionColType,
)


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================


# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "apeqpt",
        sa.Column(
            "q_datetime",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("q1_choice", sa.Integer(), nullable=True),
        sa.Column("q2_choice", sa.Integer(), nullable=True),
        sa.Column("q3_choice", sa.Integer(), nullable=True),
        sa.Column("q1_satisfaction", sa.Integer(), nullable=True),
        sa.Column("q2_satisfaction", sa.UnicodeText(), nullable=True),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("firstexit_is_finish", sa.Boolean(), nullable=True),
        sa.Column("firstexit_is_abort", sa.Boolean(), nullable=True),
        sa.Column("editing_time_s", sa.Float(), nullable=True),
        sa.Column("_pk", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("_device_id", sa.Integer(), nullable=False),
        sa.Column("_era", sa.String(length=32), nullable=False),
        sa.Column("_current", sa.Boolean(), nullable=False),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_added_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_adding_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_removed_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_removing_user_id", sa.Integer(), nullable=True),
        sa.Column("_preserving_user_id", sa.Integer(), nullable=True),
        sa.Column("_forcibly_preserved", sa.Boolean(), nullable=True),
        sa.Column("_predecessor_pk", sa.Integer(), nullable=True),
        sa.Column("_successor_pk", sa.Integer(), nullable=True),
        sa.Column("_manually_erased", sa.Boolean(), nullable=True),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_manually_erasing_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
        ),
        sa.Column("_addition_pending", sa.Boolean(), nullable=False),
        sa.Column("_removal_pending", sa.Boolean(), nullable=True),
        sa.Column("_group_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_move_off_tablet", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_apeqpt__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_apeqpt__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_apeqpt__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_apeqpt__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_apeqpt__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_apeqpt__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_apeqpt")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("apeqpt", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_apeqpt__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apeqpt__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apeqpt__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apeqpt__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_apeqpt__pk"), ["_pk"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_apeqpt_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_apeqpt_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    op.create_table(
        "gbogres",
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("goal_1_description", sa.UnicodeText(), nullable=True),
        sa.Column("goal_2_description", sa.UnicodeText(), nullable=True),
        sa.Column("goal_3_description", sa.UnicodeText(), nullable=True),
        sa.Column("other_goals", sa.UnicodeText(), nullable=True),
        sa.Column("completed_by", sa.Integer(), nullable=True),
        sa.Column("completed_by_other", sa.UnicodeText(), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("firstexit_is_finish", sa.Boolean(), nullable=True),
        sa.Column("firstexit_is_abort", sa.Boolean(), nullable=True),
        sa.Column("editing_time_s", sa.Float(), nullable=True),
        sa.Column("_pk", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("_device_id", sa.Integer(), nullable=False),
        sa.Column("_era", sa.String(length=32), nullable=False),
        sa.Column("_current", sa.Boolean(), nullable=False),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_added_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_adding_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_removed_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_removing_user_id", sa.Integer(), nullable=True),
        sa.Column("_preserving_user_id", sa.Integer(), nullable=True),
        sa.Column("_forcibly_preserved", sa.Boolean(), nullable=True),
        sa.Column("_predecessor_pk", sa.Integer(), nullable=True),
        sa.Column("_successor_pk", sa.Integer(), nullable=True),
        sa.Column("_manually_erased", sa.Boolean(), nullable=True),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_manually_erasing_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
        ),
        sa.Column("_addition_pending", sa.Boolean(), nullable=False),
        sa.Column("_removal_pending", sa.Boolean(), nullable=True),
        sa.Column("_group_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_move_off_tablet", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_gbogres__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_gbogres__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_gbogres__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_gbogres__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_gbogres__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_gbogres__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_gbogres")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("gbogres", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_gbogres__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres__pk"), ["_pk"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_gbogres_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    op.create_table(
        "ors",
        sa.Column("q_session", sa.Integer(), nullable=True),
        sa.Column("q_date", sa.Date(), nullable=True),
        sa.Column("q_who", sa.Integer(), nullable=True),
        sa.Column("q_who_other", sa.UnicodeText(), nullable=True),
        sa.Column("q_individual", sa.Float(), nullable=True),
        sa.Column("q_interpersonal", sa.Float(), nullable=True),
        sa.Column("q_social", sa.Float(), nullable=True),
        sa.Column("q_overall", sa.Float(), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("firstexit_is_finish", sa.Boolean(), nullable=True),
        sa.Column("firstexit_is_abort", sa.Boolean(), nullable=True),
        sa.Column("editing_time_s", sa.Float(), nullable=True),
        sa.Column("_pk", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("_device_id", sa.Integer(), nullable=False),
        sa.Column("_era", sa.String(length=32), nullable=False),
        sa.Column("_current", sa.Boolean(), nullable=False),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_added_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_adding_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_removed_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_removing_user_id", sa.Integer(), nullable=True),
        sa.Column("_preserving_user_id", sa.Integer(), nullable=True),
        sa.Column("_forcibly_preserved", sa.Boolean(), nullable=True),
        sa.Column("_predecessor_pk", sa.Integer(), nullable=True),
        sa.Column("_successor_pk", sa.Integer(), nullable=True),
        sa.Column("_manually_erased", sa.Boolean(), nullable=True),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_manually_erasing_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
        ),
        sa.Column("_addition_pending", sa.Boolean(), nullable=False),
        sa.Column("_removal_pending", sa.Boolean(), nullable=True),
        sa.Column("_group_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_move_off_tablet", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_ors__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_ors__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_ors__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_ors__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_ors__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_ors__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_ors")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("ors", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_ors__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_ors__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_ors__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_ors__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_ors__pk"), ["_pk"], unique=False)
        batch_op.create_index(batch_op.f("ix_ors_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_ors_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_ors_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    op.create_table(
        "srs",
        sa.Column("q_session", sa.Integer(), nullable=True),
        sa.Column("q_date", sa.Date(), nullable=True),
        sa.Column("q_relationship", sa.Float(), nullable=True),
        sa.Column("q_goals", sa.Float(), nullable=True),
        sa.Column("q_approach", sa.Float(), nullable=True),
        sa.Column("q_overall", sa.Float(), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("firstexit_is_finish", sa.Boolean(), nullable=True),
        sa.Column("firstexit_is_abort", sa.Boolean(), nullable=True),
        sa.Column("editing_time_s", sa.Float(), nullable=True),
        sa.Column("_pk", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("_device_id", sa.Integer(), nullable=False),
        sa.Column("_era", sa.String(length=32), nullable=False),
        sa.Column("_current", sa.Boolean(), nullable=False),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_added_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_adding_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_when_removed_batch_utc", sa.DateTime(), nullable=True),
        sa.Column("_removing_user_id", sa.Integer(), nullable=True),
        sa.Column("_preserving_user_id", sa.Integer(), nullable=True),
        sa.Column("_forcibly_preserved", sa.Boolean(), nullable=True),
        sa.Column("_predecessor_pk", sa.Integer(), nullable=True),
        sa.Column("_successor_pk", sa.Integer(), nullable=True),
        sa.Column("_manually_erased", sa.Boolean(), nullable=True),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_manually_erasing_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
        ),
        sa.Column("_addition_pending", sa.Boolean(), nullable=False),
        sa.Column("_removal_pending", sa.Boolean(), nullable=True),
        sa.Column("_group_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
        ),
        sa.Column("_move_off_tablet", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_srs__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_srs__device_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_srs__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_srs__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_srs__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_srs__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_srs")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("srs", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_srs__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_srs__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_srs__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_srs__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_srs__pk"), ["_pk"], unique=False)
        batch_op.create_index(batch_op.f("ix_srs_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_srs_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_srs_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    # ### end Alembic commands ###


def downgrade():
    op.drop_table("srs")
    op.drop_table("ors")
    op.drop_table("gbogres")
    op.drop_table("apeqpt")
