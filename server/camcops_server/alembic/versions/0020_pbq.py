#!/usr/bin/env python

"""
camcops_server/alembic/versions/0020_pbq.py

===============================================================================

    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

PBQ - Postpartum Bonding Questionnaire

Revision ID: 0020
Revises: 0019
Creation date: 2019-04-01 23:52:57.174006

"""

# =============================================================================
# Imports
# =============================================================================

from alembic import op
import sqlalchemy as sa
import camcops_server.cc_modules.cc_sqla_coltypes


# =============================================================================
# Revision identifiers, used by Alembic.
# =============================================================================

revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


# =============================================================================
# The upgrade/downgrade steps
# =============================================================================

# noinspection PyPep8,PyTypeChecker
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pbq',
        sa.Column('q1', sa.Integer(), nullable=True, comment='Q1, I feel close to my baby (always 0 - never 5, higher worse)'),
        sa.Column('q2', sa.Integer(), nullable=True, comment='Q2, I wish the old days when I had no baby would come back (always 5 - never 0, higher worse)'),
        sa.Column('q3', sa.Integer(), nullable=True, comment='Q3, I feel distant from my baby (always 5 - never 0, higher worse)'),
        sa.Column('q4', sa.Integer(), nullable=True, comment='Q4, I love to cuddle my baby (always 0 - never 5, higher worse)'),
        sa.Column('q5', sa.Integer(), nullable=True, comment='Q5, I regret having this baby (always 5 - never 0, higher worse)'),
        sa.Column('q6', sa.Integer(), nullable=True, comment='Q6, The baby does not seem to be mine (always 5 - never 0, higher worse)'),
        sa.Column('q7', sa.Integer(), nullable=True, comment='Q7, My baby winds me up (always 5 - never 0, higher worse)'),
        sa.Column('q8', sa.Integer(), nullable=True, comment='Q8, I love my baby to bits (always 0 - never 5, higher worse)'),
        sa.Column('q9', sa.Integer(), nullable=True, comment='Q9, I feel happy when my baby smiles or laughs (always 0 - never 5, higher worse)'),
        sa.Column('q10', sa.Integer(), nullable=True, comment='Q10, My baby irritates me (always 5 - never 0, higher worse)'),
        sa.Column('q11', sa.Integer(), nullable=True, comment='Q11, I enjoy playing with my baby (always 0 - never 5, higher worse)'),
        sa.Column('q12', sa.Integer(), nullable=True, comment='Q12, My baby cries too much (always 5 - never 0, higher worse)'),
        sa.Column('q13', sa.Integer(), nullable=True, comment='Q13, I feel trapped as a mother (always 5 - never 0, higher worse)'),
        sa.Column('q14', sa.Integer(), nullable=True, comment='Q14, I feel angry with my baby (always 5 - never 0, higher worse)'),
        sa.Column('q15', sa.Integer(), nullable=True, comment='Q15, I resent my baby (always 5 - never 0, higher worse)'),
        sa.Column('q16', sa.Integer(), nullable=True, comment='Q16, My baby is the most beautiful baby in the world (always 0 - never 5, higher worse)'),
        sa.Column('q17', sa.Integer(), nullable=True, comment='Q17, I wish my baby would somehow go away (always 5 - never 0, higher worse)'),
        sa.Column('q18', sa.Integer(), nullable=True, comment='Q18, I have done harmful things to my baby (always 5 - never 0, higher worse)'),
        sa.Column('q19', sa.Integer(), nullable=True, comment='Q19, My baby makes me anxious (always 5 - never 0, higher worse)'),
        sa.Column('q20', sa.Integer(), nullable=True, comment='Q20, I am afraid of my baby (always 5 - never 0, higher worse)'),
        sa.Column('q21', sa.Integer(), nullable=True, comment='Q21, My baby annoys me (always 5 - never 0, higher worse)'),
        sa.Column('q22', sa.Integer(), nullable=True, comment='Q22, I feel confident when changing my baby (always 0 - never 5, higher worse)'),
        sa.Column('q23', sa.Integer(), nullable=True, comment='Q23, I feel the only solution is for someone else to look after my baby (always 5 - never 0, higher worse)'),
        sa.Column('q24', sa.Integer(), nullable=True, comment='Q24, I feel like hurting my baby (always 5 - never 0, higher worse)'),
        sa.Column('q25', sa.Integer(), nullable=True, comment='Q25, My baby is easily comforted (always 0 - never 5, higher worse)'),
        sa.Column('patient_id', sa.Integer(), nullable=False, comment='(TASK) Foreign key to patient.id (for this device/era)'),
        sa.Column('when_created', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=False, comment='(TASK) Date/time this task instance was created (ISO 8601)'),
        sa.Column('when_firstexit', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(TASK) Date/time of the first exit from this task (ISO 8601)'),
        sa.Column('firstexit_is_finish', sa.Boolean(), nullable=True, comment='(TASK) Was the first exit from the task because it was finished (1)?'),
        sa.Column('firstexit_is_abort', sa.Boolean(), nullable=True, comment='(TASK) Was the first exit from this task because it was aborted (1)?'),
        sa.Column('editing_time_s', sa.Float(), nullable=True, comment='(TASK) Time spent editing (s)'),
        sa.Column('_pk', sa.Integer(), autoincrement=True, nullable=False, comment='(SERVER) Primary key (on the server)'),
        sa.Column('_device_id', sa.Integer(), nullable=False, comment='(SERVER) ID of the source tablet device'),
        sa.Column('_era', sa.String(length=32), nullable=False, comment="(SERVER) 'NOW', or when this row was preserved and removed from the source device (UTC ISO 8601)"),
        sa.Column('_current', sa.Boolean(), nullable=False, comment='(SERVER) Is the row current (1) or not (0)?'),
        sa.Column('_when_added_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time this row was added (ISO 8601)'),
        sa.Column('_when_added_batch_utc', sa.DateTime(), nullable=True, comment='(SERVER) Date/time of the upload batch that added this row (DATETIME in UTC)'),
        sa.Column('_adding_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that added this row'),
        sa.Column('_when_removed_exact', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time this row was removed, i.e. made not current (ISO 8601)'),
        sa.Column('_when_removed_batch_utc', sa.DateTime(), nullable=True, comment='(SERVER) Date/time of the upload batch that removed this row (DATETIME in UTC)'),
        sa.Column('_removing_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that removed this row'),
        sa.Column('_preserving_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that preserved this row'),
        sa.Column('_forcibly_preserved', sa.Boolean(), nullable=True, comment='(SERVER) Forcibly preserved by superuser (rather than normally preserved by tablet)?'),
        sa.Column('_predecessor_pk', sa.Integer(), nullable=True, comment='(SERVER) PK of predecessor record, prior to modification'),
        sa.Column('_successor_pk', sa.Integer(), nullable=True, comment='(SERVER) PK of successor record  (after modification) or NULL (whilst live, or after deletion)'),
        sa.Column('_manually_erased', sa.Boolean(), nullable=True, comment='(SERVER) Record manually erased (content destroyed)?'),
        sa.Column('_manually_erased_at', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(SERVER) Date/time of manual erasure (ISO 8601)'),
        sa.Column('_manually_erasing_user_id', sa.Integer(), nullable=True, comment='(SERVER) ID of user that erased this row manually'),
        sa.Column('_camcops_version', camcops_server.cc_modules.cc_sqla_coltypes.SemanticVersionColType(length=147), nullable=True, comment='(SERVER) CamCOPS version number of the uploading device'),
        sa.Column('_addition_pending', sa.Boolean(), nullable=False, comment='(SERVER) Addition pending?'),
        sa.Column('_removal_pending', sa.Boolean(), nullable=True, comment='(SERVER) Removal pending?'),
        sa.Column('_group_id', sa.Integer(), nullable=False, comment='(SERVER) ID of group to which this record belongs'),
        sa.Column('id', sa.Integer(), nullable=False, comment='(TASK) Primary key (task ID) on the tablet device'),
        sa.Column('when_last_modified', camcops_server.cc_modules.cc_sqla_coltypes.PendulumDateTimeAsIsoTextColType(length=32), nullable=True, comment='(STANDARD) Date/time this row was last modified on the source tablet device (ISO 8601)'),
        sa.Column('_move_off_tablet', sa.Boolean(), nullable=True, comment='(SERVER/TABLET) Record-specific preservation pending?'),
        sa.ForeignKeyConstraint(['_adding_user_id'], ['_security_users.id'], name=op.f('fk_pbq__adding_user_id')),
        sa.ForeignKeyConstraint(['_device_id'], ['_security_devices.id'], name=op.f('fk_pbq__device_id')),
        sa.ForeignKeyConstraint(['_group_id'], ['_security_groups.id'], name=op.f('fk_pbq__group_id')),
        sa.ForeignKeyConstraint(['_manually_erasing_user_id'], ['_security_users.id'], name=op.f('fk_pbq__manually_erasing_user_id')),
        sa.ForeignKeyConstraint(['_preserving_user_id'], ['_security_users.id'], name=op.f('fk_pbq__preserving_user_id')),
        sa.ForeignKeyConstraint(['_removing_user_id'], ['_security_users.id'], name=op.f('fk_pbq__removing_user_id')),
        sa.PrimaryKeyConstraint('_pk', name=op.f('pk_pbq')),
        mysql_charset='utf8mb4 COLLATE utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        mysql_row_format='DYNAMIC'
    )
    with op.batch_alter_table('pbq', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pbq__current'), ['_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq__device_id'), ['_device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq__era'), ['_era'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq__group_id'), ['_group_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq__pk'), ['_pk'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pbq_when_last_modified'), ['when_last_modified'], unique=False)


def downgrade():
    op.drop_table('pbq')
