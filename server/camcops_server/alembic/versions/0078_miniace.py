#!/usr/bin/env python

"""
camcops_server/alembic/versions/0078_miniace.py

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

Mini-ACE and extensions to ACE-III

Revision ID: 0078
Revises: 0077
Creation date: 2022-12-08 17:18:23.099283

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

revision = "0078"
down_revision = "0077"
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "miniace",
        sa.Column(
            "task_edition",
            sa.String(length=255),
            nullable=True,
            comment="Task edition.",
        ),
        sa.Column(
            "task_address_version",
            sa.String(length=1),
            nullable=True,
            comment="Task version, determining the address for recall "
            "(A/B/C).",
        ),
        sa.Column(
            "remote_administration",
            sa.Boolean(),
            nullable=True,
            comment="Task performed using remote (videoconferencing) "
            "administration?",
        ),
        sa.Column(
            "age_at_leaving_full_time_education",
            sa.Integer(),
            nullable=True,
            comment="Age at leaving full time education",
        ),
        sa.Column(
            "occupation", sa.UnicodeText(), nullable=True, comment="Occupation"
        ),
        sa.Column(
            "handedness",
            sa.String(length=1),
            nullable=True,
            comment="Handedness (L or R)",
        ),
        sa.Column(
            "fluency_animals_score",
            sa.Integer(),
            nullable=True,
            comment="Fluency, animals, score 0-7",
        ),
        sa.Column(
            "vsp_draw_clock",
            sa.Integer(),
            nullable=True,
            comment="Visuospatial, draw clock (0-5)",
        ),
        sa.Column(
            "picture1_blobid",
            sa.Integer(),
            nullable=True,
            comment="Photo 1/2 PNG BLOB ID",
        ),
        sa.Column(
            "picture2_blobid",
            sa.Integer(),
            nullable=True,
            comment="Photo 2/2 PNG BLOB ID",
        ),
        sa.Column(
            "comments",
            sa.UnicodeText(),
            nullable=True,
            comment="Clinician's comments",
        ),
        sa.Column(
            "attn_time1",
            sa.Integer(),
            nullable=True,
            comment="Attention, time, 1/4, day (0 or 1)",
        ),
        sa.Column(
            "attn_time2",
            sa.Integer(),
            nullable=True,
            comment="Attention, time, 2/4, date (0 or 1)",
        ),
        sa.Column(
            "attn_time3",
            sa.Integer(),
            nullable=True,
            comment="Attention, time, 3/4, month (0 or 1)",
        ),
        sa.Column(
            "attn_time4",
            sa.Integer(),
            nullable=True,
            comment="Attention, time, 4/4, year (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_1",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "forename (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_2",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "surname (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_3",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "number (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_4",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "street_1 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_5",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "street_2 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_6",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "town (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial1_7",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 1/3 (not scored), "
            "county (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_1",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "forename (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_2",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "surname (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_3",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "number (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_4",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "street_1 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_5",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "street_2 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_6",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "town (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial2_7",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 2/3 (not scored), "
            "county (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_1",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), "
            "forename (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_2",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), surname "
            "(0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_3",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), number "
            "(0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_4",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), "
            "street_1 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_5",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), "
            "street_2 (0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_6",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), town "
            "(0 or 1)",
        ),
        sa.Column(
            "mem_repeat_address_trial3_7",
            sa.Integer(),
            nullable=True,
            comment="Memory, address registration trial 3/3 (scored), county "
            "(0 or 1)",
        ),
        sa.Column(
            "mem_recall_address1",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 1/7, forename (0-1)",
        ),
        sa.Column(
            "mem_recall_address2",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 2/7, surname (0-1)",
        ),
        sa.Column(
            "mem_recall_address3",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 3/7, number (0-1)",
        ),
        sa.Column(
            "mem_recall_address4",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 4/7, street_1 (0-1)",
        ),
        sa.Column(
            "mem_recall_address5",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 5/7, street_2 (0-1)",
        ),
        sa.Column(
            "mem_recall_address6",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 6/7, town (0-1)",
        ),
        sa.Column(
            "mem_recall_address7",
            sa.Integer(),
            nullable=True,
            comment="Memory, recall address 7/7, county (0-1)",
        ),
        sa.Column(
            "patient_id",
            sa.Integer(),
            nullable=False,
            comment="(TASK) Foreign key to patient.id (for this device/era)",
        ),
        sa.Column(
            "clinician_specialty",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's specialty (e.g. Liaison "
            "Psychiatry)",
        ),
        sa.Column(
            "clinician_name",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's name (e.g. Dr X)",
        ),
        sa.Column(
            "clinician_professional_registration",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's professional registration (e.g. "
            "GMC# 12345)",
        ),
        sa.Column(
            "clinician_post",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's post (e.g. Consultant)",
        ),
        sa.Column(
            "clinician_service",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's service (e.g. Liaison Psychiatry "
            "Service)",
        ),
        sa.Column(
            "clinician_contact_details",
            sa.Text(),
            nullable=True,
            comment="(CLINICIAN) Clinician's contact details (e.g. bleep, "
            "extension)",
        ),
        sa.Column(
            "when_created",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=False,
            comment="(TASK) Date/time this task instance was created (ISO "
            "8601)",
        ),
        sa.Column(
            "when_firstexit",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(TASK) Date/time of the first exit from this task (ISO "
            "8601)",
        ),
        sa.Column(
            "firstexit_is_finish",
            sa.Boolean(),
            nullable=True,
            comment="(TASK) Was the first exit from the task because it was "
            "finished (1)?",
        ),
        sa.Column(
            "firstexit_is_abort",
            sa.Boolean(),
            nullable=True,
            comment="(TASK) Was the first exit from this task because it was "
            "aborted (1)?",
        ),
        sa.Column(
            "editing_time_s",
            sa.Float(),
            nullable=True,
            comment="(TASK) Time spent editing (s)",
        ),
        sa.Column(
            "_pk",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="(SERVER) Primary key (on the server)",
        ),
        sa.Column(
            "_device_id",
            sa.Integer(),
            nullable=False,
            comment="(SERVER) ID of the source tablet device",
        ),
        sa.Column(
            "_era",
            sa.String(length=32),
            nullable=False,
            comment="(SERVER) 'NOW', or when this row was preserved and "
            "removed from the source device (UTC ISO 8601)",
        ),
        sa.Column(
            "_current",
            sa.Boolean(),
            nullable=False,
            comment="(SERVER) Is the row current (1) or not (0)?",
        ),
        sa.Column(
            "_when_added_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(SERVER) Date/time this row was added (ISO 8601)",
        ),
        sa.Column(
            "_when_added_batch_utc",
            sa.DateTime(),
            nullable=True,
            comment="(SERVER) Date/time of the upload batch that added this "
            "row (DATETIME in UTC)",
        ),
        sa.Column(
            "_adding_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that added this row",
        ),
        sa.Column(
            "_when_removed_exact",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(SERVER) Date/time this row was removed, i.e. made not "
            "current (ISO 8601)",
        ),
        sa.Column(
            "_when_removed_batch_utc",
            sa.DateTime(),
            nullable=True,
            comment="(SERVER) Date/time of the upload batch that removed this "
            "row (DATETIME in UTC)",
        ),
        sa.Column(
            "_removing_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that removed this row",
        ),
        sa.Column(
            "_preserving_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that preserved this row",
        ),
        sa.Column(
            "_forcibly_preserved",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER) Forcibly preserved by superuser (rather than "
            "normally preserved by tablet)?",
        ),
        sa.Column(
            "_predecessor_pk",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) PK of predecessor record, prior to modification",
        ),
        sa.Column(
            "_successor_pk",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) PK of successor record  (after modification) or "
            "NULL (whilst live, or after deletion)",
        ),
        sa.Column(
            "_manually_erased",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER) Record manually erased (content destroyed)?",
        ),
        sa.Column(
            "_manually_erased_at",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(SERVER) Date/time of manual erasure (ISO 8601)",
        ),
        sa.Column(
            "_manually_erasing_user_id",
            sa.Integer(),
            nullable=True,
            comment="(SERVER) ID of user that erased this row manually",
        ),
        sa.Column(
            "_camcops_version",
            SemanticVersionColType(length=147),
            nullable=True,
            comment="(SERVER) CamCOPS version number of the uploading device",
        ),
        sa.Column(
            "_addition_pending",
            sa.Boolean(),
            nullable=False,
            comment="(SERVER) Addition pending?",
        ),
        sa.Column(
            "_removal_pending",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER) Removal pending?",
        ),
        sa.Column(
            "_group_id",
            sa.Integer(),
            nullable=False,
            comment="(SERVER) ID of group to which this record belongs",
        ),
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            comment="(TASK) Primary key (task ID) on the tablet device",
        ),
        sa.Column(
            "when_last_modified",
            PendulumDateTimeAsIsoTextColType(length=32),
            nullable=True,
            comment="(STANDARD) Date/time this row was last modified on the "
            "source tablet device (ISO 8601)",
        ),
        sa.Column(
            "_move_off_tablet",
            sa.Boolean(),
            nullable=True,
            comment="(SERVER/TABLET) Record-specific preservation pending?",
        ),
        sa.ForeignKeyConstraint(
            ["_adding_user_id"],
            ["_security_users.id"],
            name=op.f("fk_miniace__adding_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_device_id"],
            ["_security_devices.id"],
            name=op.f("fk_miniace__device_id"),
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["_group_id"],
            ["_security_groups.id"],
            name=op.f("fk_miniace__group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_manually_erasing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_miniace__manually_erasing_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_preserving_user_id"],
            ["_security_users.id"],
            name=op.f("fk_miniace__preserving_user_id"),
        ),
        sa.ForeignKeyConstraint(
            ["_removing_user_id"],
            ["_security_users.id"],
            name=op.f("fk_miniace__removing_user_id"),
        ),
        sa.PrimaryKeyConstraint("_pk", name=op.f("pk_miniace")),
        mysql_charset="utf8mb4 COLLATE utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        mysql_row_format="DYNAMIC",
    )
    with op.batch_alter_table("miniace", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_miniace__current"), ["_current"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace__device_id"), ["_device_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace__era"), ["_era"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace__group_id"), ["_group_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace__pk"), ["_pk"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace_id"), ["id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace_patient_id"), ["patient_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_miniace_when_last_modified"),
            ["when_last_modified"],
            unique=False,
        )

    # https://github.com/sqlalchemy/alembic/issues/326
    with op.batch_alter_table("miniace", schema=None) as batch_op:
        batch_op.create_foreign_key(
            batch_op.f("fk_miniace__device_id"),
            "_security_devices",
            ["_device_id"],
            ["id"],
            use_alter=True,
        )

    with op.batch_alter_table("ace3", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "remote_administration",
                sa.Boolean(),
                nullable=True,
                comment="Task performed using remote (videoconferencing) "
                "administration?",
            )
        )
        batch_op.add_column(
            sa.Column(
                "task_address_version",
                sa.String(length=1),
                nullable=True,
                comment="Task version, determining the address for recall "
                "(A/B/C). Older task instances will have NULL and that "
                "indicates version A.",
            )
        )
        batch_op.add_column(
            sa.Column(
                "task_edition",
                sa.String(length=255),
                nullable=True,
                comment="Task edition. Older task instances will have NULL "
                "and that indicates UK English, 2012 version.",
            )
        )
        batch_op.drop_column("picture2_rotation")
        batch_op.drop_column("picture1_rotation")


# noinspection PyPep8,PyTypeChecker
def downgrade():
    with op.batch_alter_table("ace3", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "picture1_rotation",
                sa.Integer(),
                autoincrement=False,
                nullable=True,
                comment="Photo 1/2 rotation (degrees clockwise)",
            )
        )
        batch_op.add_column(
            sa.Column(
                "picture2_rotation",
                sa.Integer(),
                autoincrement=False,
                nullable=True,
                comment="Photo 2/2 rotation (degrees clockwise)",
            )
        )
        batch_op.drop_column("task_edition")
        batch_op.drop_column("task_address_version")
        batch_op.drop_column("remote_administration")

    op.drop_table("miniace")
