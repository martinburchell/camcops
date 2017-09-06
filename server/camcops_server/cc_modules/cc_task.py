#!/usr/bin/env python
# camcops_server/cc_modules/cc_task.py

"""
===============================================================================
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

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
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================

NOTES:
    Core export methods:
    - HTML
        ... the task in a user-friendly format
    - PDF = essentially the HTML output
    - XML
        ... centres on the task with its subdata integrated
    - TSV summary
    - CRIS summary
        ... table-based, but all records include patient ID
    - classmethods to make summary tables
"""

import collections
import copy
import datetime
import logging
import statistics
import typing
from typing import (Any, Dict, Iterable, Generator, List, Optional, Sequence,
                    Tuple, Type, TYPE_CHECKING, Union)

from cardinal_pythonlib.classes import (
    all_subclasses,
    classproperty,
    derived_class_implements_method,
)
from cardinal_pythonlib.lists import flatten_list
from cardinal_pythonlib.logs import BraceStyleAdapter
from cardinal_pythonlib.rnc_db import DatabaseSupporter, FIELDSPECLIST_TYPE
import cardinal_pythonlib.rnc_web as ws
from cardinal_pythonlib.sqlalchemy.core_query import (
    get_rows_fieldnames_from_raw_sql,
)
from cardinal_pythonlib.sqlalchemy.orm_inspect import gen_columns
from cardinal_pythonlib.sqlalchemy.schema import is_sqlatype_string
from cardinal_pythonlib.stringfunc import mangle_unicode_to_ascii
import hl7
from pyramid.renderers import render
from semantic_version import Version
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.elements import literal
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean, Float, Integer, Text

from .cc_anon import (
    get_cris_dd_rows_from_fieldspecs,
    get_literal_regex,
    get_type_size_as_text_from_sqltype,
)
from .cc_audit import audit
from .cc_blob import Blob, get_blob_img_html
from .cc_cache import cache_region_static, fkg
from .cc_constants import (
    ACTION,
    ANON_PATIENT,
    COMMENT_IS_COMPLETE,
    CRIS_CLUSTER_KEY_FIELDSPEC,
    CRIS_PATIENT_COMMENT_PREFIX,
    CRIS_SUMMARY_COMMENT_PREFIX,
    CRIS_TABLENAME_PREFIX,
    CSS_PAGED_MEDIA,
    DATEFORMAT,
    ERA_NOW,
    HL7MESSAGE_TABLENAME,
    INVALID_VALUE,
    PARAM,
    PKNAME,
    SIGNATURE_BLOCK,
    TSV_PATIENT_FIELD_PREFIX,
    VALUE,
)
from .cc_ctvinfo import CtvInfo
from .cc_db import GenericTabletRecordMixin
from .cc_device import Device
from .cc_dt import (
    convert_datetime_to_utc,
    get_date_regex,
    get_datetime_from_string,
    get_now_utc,
    format_datetime,
    format_datetime_string
)
from .cc_filename import get_export_filename
from .cc_hl7core import make_obr_segment, make_obx_segment
from .cc_html import (
    answer,
    get_generic_action_url,
    get_present_absent_none,
    get_true_false_none,
    get_url_field_value_pair,
    get_yes_no,
    get_yes_no_none,
    pdf_footer_content,
    pdf_header_content,
    tr,
    tr_qa,
)
from .cc_patient import Patient
from .cc_patientidnum import PatientIdNum
from .cc_pdf import pdf_from_html
from .cc_plot import set_matplotlib_fontsize
from .cc_pyramid import ViewArg
from .cc_recipdef import RecipientDefinition
from .cc_report import Report, REPORT_RESULT_TYPE
from .cc_request import CamcopsRequest
from .cc_specialnote import SpecialNote
from .cc_sqla_coltypes import (
    CamcopsColumn,
    ArrowDateTimeAsIsoTextColType,
    get_column_attr_names,
    get_camcops_blob_column_attr_names,
    permitted_value_failure_msgs,
    permitted_values_ok,
)
from .cc_sqlalchemy import Base
from .cc_summaryelement import SummaryElement
from .cc_trackerhelpers import TrackerInfo
from .cc_unittest import (
    get_object_name,
    unit_test_ignore,
    unit_test_require_truthy_attribute,
    unit_test_show,
    unit_test_verify,
    unit_test_verify_not
)
from .cc_user import User
from .cc_version import CAMCOPS_SERVER_VERSION, make_version
from .cc_xml import (
    get_xml_blob_tuple,
    get_xml_document,
    make_xml_branches_from_fieldspecs,
    make_xml_branches_from_summaries,
    XML_COMMENT_ANONYMOUS,
    XML_COMMENT_BLOBS,
    XML_COMMENT_CALCULATED,
    XML_COMMENT_PATIENT,
    XML_COMMENT_SPECIAL_NOTES,
    XML_COMMENT_STORED,
    XmlElement,
)

if TYPE_CHECKING:
    from .cc_session import CamcopsSession

log = BraceStyleAdapter(logging.getLogger(__name__))

ANCILLARY_FWD_REF = "Ancillary"
TASK_FWD_REF = "Task"


# =============================================================================
# Patient mixin
# =============================================================================

class TaskHasPatientMixin(object):
    # http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#using-advanced-relationship-arguments-e-g-primaryjoin-etc  # noqa

    # noinspection PyMethodParameters
    @declared_attr
    def patient_id(cls) -> Column:
        return Column(
            "patient_id", Integer,
            nullable=False, index=True,
            comment="(TASK) Foreign key to patient.id (for this device/era)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def patient(cls) -> RelationshipProperty:
        return relationship(
            "Patient",
            primaryjoin=(
                "and_("
                " remote(Patient.id) == foreign({task}.patient_id), "
                " remote(Patient._device_id) == foreign({task}._device_id), "
                " remote(Patient._era) == foreign({task}._era), "
                " remote(Patient._current) == True "
                ")".format(
                    task=cls.__name__,
                )
            ),
            uselist=False,
            viewonly=True,
            lazy="joined"
        )
        # NOTE: this retrieves the most recent (i.e. the current) information
        # on that patient. Consequently, task version history doesn't show the
        # history of patient edits. This is consistent with our relationship
        # strategy throughout for the web front-end viewer.

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        return True


# =============================================================================
# Clinician mixin
# =============================================================================

class TaskHasClinicianMixin(object):
    """
    Mixin to add clinician columns and override clinician-related methods.
    Must be to the LEFT of Task in the class's base class list.
    """
    # noinspection PyMethodParameters
    @declared_attr
    def clinician_specialty(cls) -> Column:
        return CamcopsColumn(
            "clinician_specialty", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's specialty "
                    "(e.g. Liaison Psychiatry)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_name(cls) -> Column:
        return CamcopsColumn(
            "clinician_name", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's name (e.g. Dr X)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_professional_registration(cls) -> Column:
        return Column(
            "clinician_professional_registration", Text,
            comment="(CLINICIAN) Clinician's professional registration (e.g. "
                    "GMC# 12345)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_post(cls) -> Column:
        return CamcopsColumn(
            "clinician_post", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's post (e.g. Consultant)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_service(cls) -> Column:
        return CamcopsColumn(
            "clinician_service", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's service (e.g. Liaison Psychiatry "
                    "Service)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def clinician_contact_details(cls) -> Column:
        return CamcopsColumn(
            "clinician_contact_details", Text,
            exempt_from_anonymisation=True,
            comment="(CLINICIAN) Clinician's contact details (e.g. bleep, "
                    "extension)"
        )

    # For field order, see also:
    # https://stackoverflow.com/questions/3923910/sqlalchemy-move-mixin-columns-to-end  # noqa

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        return True

    def get_clinician_name(self) -> str:
        return self.clinician_name


# =============================================================================
# Respondent mixin
# =============================================================================

class TaskHasRespondentMixin(object):
    """
    Mixin to add respondent columns and override respondent-related methods.
    Must be to the LEFT of Task in the class's base class list.

    If you don't use declared_attr, the "comment" property doesn't work.
    """

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_name(cls) -> Column:
        return CamcopsColumn(
            "respondent_name", Text,
            identifies_patient=True,
            comment="(RESPONDENT) Respondent's name"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def respondent_relationship(cls) -> Column:
        return Column(
            "respondent_relationship", Text,
            comment="(RESPONDENT) Respondent's relationship to patient"
        )

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        return True

    def is_respondent_complete(self) -> bool:
        return self.respondent_name and self.respondent_relationship


# =============================================================================
# Task base class
# =============================================================================

class Task(GenericTabletRecordMixin, Base):
    """
    Abstract base class for all tasks.

    - Column definitions:

        Use CamcopsColumn, not Column, if you have fields that need to define
        permitted values, mark them as BLOB-referencing fields, or do other
        CamCOPS-specific things.

    - Overridable attributes:

        dependent_classes
            Override this if your task uses sub-tables (or sub-sub-tables,
            etc.). Give a list of classes that inherit from Ancillary, e.g.

                dependent_classes = [ClassRepresentingObject]

            Each class MUST derive from Ancillary, overriding: ********
                tablename
                fieldspecs
                fkname  # FK to main task table

        extra_summary_table_info *************
            Does the task provide extra summary tables? If so, override.
            Example:

                extra_summary_table_info = [
                    {
                        tablename: XXX,
                        fieldspecs: [ ... ]
                    },
                    {
                        tablename: XXX,
                        fieldspecs: [ ... ]
                    },
                ]
    """
    __abstract__ = True

    # noinspection PyMethodParameters
    @declared_attr
    def __mapper_args__(cls):
        return {
            'polymorphic_identity': cls.__name__,
            'concrete': True,
        }

    # =========================================================================
    # PART 0: COLUMNS COMMON TO ALL TASKS
    # =========================================================================

    # Columns

    # noinspection PyMethodParameters
    @declared_attr
    def when_created(cls) -> Column:
        return Column(
            "when_created", ArrowDateTimeAsIsoTextColType,
            nullable=False,
            comment="(TASK) Date/time this task instance was created (ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def when_firstexit(cls) -> Column:
        return Column(
            "when_firstexit", ArrowDateTimeAsIsoTextColType,
            comment="(TASK) Date/time of the first exit from this task "
                    "(ISO 8601)"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_finish(cls) -> Column:
        return Column(
            "firstexit_is_finish", Boolean,
            comment="(TASK) Was the first exit from the task because it was "
                    "finished (1)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def firstexit_is_abort(cls) -> Column:
        return Column(
            "firstexit_is_abort", Boolean,
            comment="(TASK) Was the first exit from this task because it was "
                    "aborted (1)?"
        )

    # noinspection PyMethodParameters
    @declared_attr
    def editing_time_s(cls) -> Column:
        return Column(
            "editing_time_s", Float,
            comment="(TASK) Time spent editing (s)"
        )

    # Relationships

    # noinspection PyMethodParameters
    @declared_attr
    def special_notes(cls) -> RelationshipProperty:
        return relationship(
            SpecialNote,
            primaryjoin=(
                "and_("
                " remote(SpecialNote.basetable) == literal({repr_task_tablename}), "  # noqa
                " remote(SpecialNote.task_id) == foreign({task}.id), "
                " remote(SpecialNote.device_id) == foreign({task}._device_id), "  # noqa
                " remote(SpecialNote.era) == foreign({task}._era) "
                ")".format(
                    task=cls.__name__,
                    repr_task_tablename=repr(cls.__tablename__),
                )
            ),
            uselist=True,
            order_by="SpecialNote.note_at",
            viewonly=True,  # *** for now!
        )

    # =========================================================================
    # PART 1: THINGS THAT DERIVED CLASSES MAY CARE ABOUT
    # =========================================================================

    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------
    __tablename__ = None  # type: str  # also the SQLAlchemy table name
    shortname = None  # type: str
    longname = None  # type: str

    # -------------------------------------------------------------------------
    # Attributes that can be overridden
    # -------------------------------------------------------------------------
    extrastring_taskname = None  # type: str  # if None, tablename is used instead  # noqa
    provides_trackers = False
    use_landscape_for_pdf = False
    dependent_classes = []
    extra_summary_table_info = []  # type: List[Dict[str, Any]]

    # -------------------------------------------------------------------------
    # Methods always overridden by the actual task
    # -------------------------------------------------------------------------

    def is_complete(self) -> bool:
        """
        Is the task instance complete?
        Must be overridden.
        """
        raise NotImplementedError("Task.is_complete must be overridden")

    def get_task_html(self, req: CamcopsRequest) -> str:
        """
        HTML for the main task content.
        Overridden by derived classes.
        """
        raise NotImplementedError(
            "No get_task_html() HTML generator for this task class!")

    # -------------------------------------------------------------------------
    # Dealing with ancillary items
    # -------------------------------------------------------------------------

    def get_ancillary_item_pks(self, itemclass: Type[ANCILLARY_FWD_REF]) \
            -> List[int]:
        return cc_db.get_contemporaneous_matching_field_pks_by_fk(
            itemclass.tablename, PKNAME,
            itemclass.fkname, self.id,
            self._device_id, self._era,
            self._when_added_batch_utc, self._when_removed_batch_utc
        )

    def get_ancillary_item_count(self, itemclass: Type[ANCILLARY_FWD_REF]) \
            -> int:
        return cc_db.get_contemporaneous_matching_field_pks_by_fk(
            itemclass.tablename, PKNAME,
            itemclass.fkname, self.id,
            self._device_id, self._era,
            self._when_added_batch_utc, self._when_removed_batch_utc,
            count_only=True
        )

    def get_ancillary_items(self,
                            itemclass: Type[ANCILLARY_FWD_REF],
                            sortfield: str = None) -> List[ANCILLARY_FWD_REF]:
        items = cc_db.get_contemporaneous_matching_ancillary_objects_by_fk(
            itemclass, self.id,
            self._device_id, self._era,
            self._when_added_batch_utc, self._when_removed_batch_utc
        )
        if sortfield is None:
            sortfield = itemclass.sortfield
        if sortfield:
            return sorted(items, key=lambda i: getattr(i, sortfield))
        return items

    @classmethod
    def make_tables(cls, drop_superfluous_columns: bool = False) -> None:
        """Make underlying database tables.

        OVERRIDE THIS if your task uses sub-tables AND does something more
        complex than the standard behaviour.
        """
        tasktablename = cls.tablename
        cc_db.create_standard_task_table(
            tasktablename,
            cls.get_full_fieldspecs(),
            cls.is_anonymous,
            drop_superfluous_columns=drop_superfluous_columns)

        for depclass in cls.dependent_classes:
            cc_db.create_standard_ancillary_table(
                depclass.tablename,
                depclass.get_full_fieldspecs(),
                depclass.fkname,
                tasktablename,
                drop_superfluous_columns=drop_superfluous_columns
            )

    @classmethod
    def drop_views(cls) -> None:
        # Some views below (e.g. "_withpt" views) may not exist, but that's OK
        # because we're using DROP VIEW IF EXISTS.

        # Base table
        pls.db.drop_view(cls.tablename + "_current")
        pls.db.drop_view(cls.tablename + "_current_withpt")
        # Ancillary tables
        for depclass in cls.dependent_classes:
            pls.db.drop_view(depclass.tablename + "_current")
        if not cls.is_anonymous:
            # Summary table
            summarytable = cls.get_standard_summary_table_name()
            pls.db.drop_view(summarytable + "_current")
            pls.db.drop_view(summarytable + "_current_withpt")
            # Extra summary tables
            infolist = list(cls.extra_summary_table_info)
            for i in range(len(infolist)):
                extrasummarytable = infolist[i]["tablename"]
                pls.db.drop_view(extrasummarytable + "_current")
                pls.db.drop_view(extrasummarytable + "_current_withpt")

    @classmethod
    def drop_summary_tables(cls) -> None:
        """Doesn't drop important data, but drops summaries (which can be
        rebuilt."""
        # Summary table
        summarytable = cls.get_standard_summary_table_name()
        pls.db.drop_table(summarytable)
        # Extra summary tables
        infolist = list(cls.extra_summary_table_info)
        for i in range(len(infolist)):
            extrasummarytable = infolist[i]["tablename"]
            pls.db.drop_table(extrasummarytable)

    @classmethod
    def get_extra_table_names(cls) -> List[str]:
        """Get a list of any extra tables used by the task."""
        return [depclass.tablename for depclass in cls.dependent_classes]

    # -------------------------------------------------------------------------
    # Implement if you provide trackers
    # -------------------------------------------------------------------------

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        """
        Tasks that provide quantitative information for tracking over time
        should override this and return a list of TrackerInfo, one per tracker.

        The information is read by get_all_plots_for_one_task_html() in
        cc_tracker.py -- q.v.

        Time information will be retrieved using the get_creation_datetime()
        function.
        """
        return []

    # -------------------------------------------------------------------------
    # Override to provide clinical text
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinical_text(self, req: CamcopsRequest) -> Optional[List[CtvInfo]]:
        """Tasks that provide clinical text information should override this
        to provide a list of dictionaries.

        Return None (default) for a task that doesn't provide clinical text,
        or [] for one with no information, or a list of CtvInfo objects.
        """
        return None

    # -------------------------------------------------------------------------
    # Override some of these if you provide summaries
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        """
        Return a list of summary value objects, for this database object
        (not any dependent classes/tables).
        """
        return []  # type: List[SummaryElement]

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_extra_summary_table_data(self, now: datetime.datetime) \
            -> List[List[List[Any]]]:
        """If used, must correspond exactly to extra_summary_table_info,
        but returning the data.

        LIST OF TABLES (matching tables in extra_summary_table_info),
            each containing a list of ZERO OR MORE ROWS,
                each containing a list of VALUES (matching fieldspecs above).
        """
        return []

    # -------------------------------------------------------------------------
    # Other potential overrides
    # -------------------------------------------------------------------------

    @classmethod
    def unit_tests(cls) -> None:
        """Perform unit tests on the task.

        May be overridden.
        """
        pass

    # =========================================================================
    # PART 2: INTERNALS
    # =========================================================================

    # -------------------------------------------------------------------------
    # Way to fetch all task types
    # -------------------------------------------------------------------------

    @classmethod
    def gen_all_subclasses(cls) -> Generator[Type[TASK_FWD_REF], None, None]:
        """
        We require that actual tasks are subclasses of both Task and Base

        ... so we can (a) inherit from Task to make a base class for actual
        tasks, as with PCL, HADS, HoNOS, etc.; and (b) not have those
        intermediate classes appear in the task list. Since all actual classes
        must be SQLAlchemy ORM objects inheriting from Base, that common
        inheritance is an excellent way to define them.

        ... CHANGED: things now inherit from Base/Task without necessarily
        being actual tasks; we discriminate using __abstract__ and/or
        __tablename__.
        """
        for c in all_subclasses(cls):
            # abstract = getattr(c, '__abstract__', False)
            # nope! Also true of concrete subclasses of abstract classes.
            abstract = not getattr(c, '__tablename__', None)
            if not abstract:
                yield c

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_tablename(cls) -> List[Type[TASK_FWD_REF]]:
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.tablename)
        return classes

    @classmethod
    @cache_region_static.cache_on_arguments(function_key_generator=fkg)
    def all_subclasses_by_shortname(cls) -> List[Type[TASK_FWD_REF]]:
        classes = list(cls.gen_all_subclasses())
        classes.sort(key=lambda c: c.shortname)
        return classes

    # -------------------------------------------------------------------------
    # Methods that may be overridden by mixins
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def has_patient(cls) -> bool:
        """
        May be overridden by TaskHasPatientMixin.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def is_anonymous(cls) -> bool:
        """
        Antonym for has_patient.
        """
        return not cls.has_patient

    # noinspection PyMethodParameters
    @classproperty
    def has_clinician(cls) -> bool:
        """
        May be overridden by TaskHasClinicianMixin.
        """
        return False

    # noinspection PyMethodParameters
    @classproperty
    def has_respondent(cls) -> bool:
        """
        May be overridden by TaskHasRespondentMixin.
        """
        return False

    # -------------------------------------------------------------------------
    # Other classmethods
    # -------------------------------------------------------------------------

    # noinspection PyMethodParameters
    @classproperty
    def tablename(cls) -> str:
        return cls.__tablename__

    # -------------------------------------------------------------------------
    # More on fields
    # -------------------------------------------------------------------------

    @classmethod
    def get_fieldnames(cls) -> List[str]:
        return get_column_attr_names(cls)

    def field_contents_valid(self) -> bool:
        """
        Checks field contents validity against fieldspecs.
        This is a high-speed function that doesn't bother with explanations,
        since we use it for lots of task is_complete() calculations.
        """
        return permitted_values_ok(self)

    def field_contents_invalid_because(self) -> List[str]:
        """Explains why contents are invalid."""
        return permitted_value_failure_msgs(self)

    def get_blob_fields(self) -> List[str]:
        return get_camcops_blob_column_attr_names(self)

    # -------------------------------------------------------------------------
    # Server field calculations
    # -------------------------------------------------------------------------

    def get_pk(self) -> Optional[int]:
        return self._pk

    def is_preserved(self) -> bool:
        """Is the task preserved and erased from the tablet?"""
        return self._pk is not None and self._era != ERA_NOW

    def was_forcibly_preserved(self) -> bool:
        """Was it forcibly preserved?"""
        return self._forcibly_preserved and self.is_preserved()

    def get_creation_datetime(self) -> Optional[datetime.datetime]:
        """Creation datetime, or None."""
        return get_datetime_from_string(self.when_created)

    def get_creation_datetime_utc(self) -> Optional[datetime.datetime]:
        """Creation datetime in UTC, or None."""
        localtime = self.get_creation_datetime()
        if localtime is None:
            return None
        return convert_datetime_to_utc(localtime)

    def get_seconds_from_creation_to_first_finish(self) -> Optional[float]:
        """Time in seconds from creation time to first finish (i.e. first exit
        if the first exit was a finish rather than an abort), or None."""
        if not self.firstexit_is_finish:
            return None
        start = self.get_creation_datetime()
        end = get_datetime_from_string(self.when_firstexit)
        if not start or not end:
            return None
        diff = end - start
        return diff.total_seconds()

    def get_adding_user_id(self) -> int:
        return self._adding_user_id

    def get_adding_user_username(self) -> str:
        return self._adding_user.username if self._adding_user else ""

    def get_removing_user_username(self) -> str:
        return self._removing_user.username if self._removing_user else ""

    def get_preserving_user_username(self) -> str:
        return self._preserving_user.username if self._preserving_user else ""

    def get_manually_erasing_user_username(self) -> str:
        return self._manually_erasing_user.username if self._manually_erasing_user else ""  # noqa

    # -------------------------------------------------------------------------
    # Summary tables
    # -------------------------------------------------------------------------

    @classmethod
    def get_standard_summary_table_name(cls) -> str:
        """Returns the main summary table for the task."""
        return cls.tablename + "_SUMMARY_TEMP"

    @classmethod
    def provides_summaries(cls, req: CamcopsRequest) -> bool:
        """Does the task provide summary information?"""
        specimen_instance = cls(None)  # blank PK
        return len(specimen_instance.get_summaries(req)) > 0

    @classmethod
    def make_summary_table(cls) -> None:
        """Drop and remake (temporary) summary tables."""
        # now = get_now_utc()
        cls.drop_summary_tables()

        # DISABLED FOR NOW:
        # cls.make_standard_summary_table(now)
        # cls.make_extra_summary_tables(now)
        # # ... in case the task wants to make extra tables

    @classmethod
    def make_standard_summary_table(cls,
                                    req: CamcopsRequest,
                                    now: datetime.datetime) -> None:
        """Make the task's main summary table."""
        table = cls.tablename
        if not cls.provides_summaries(req):
            return
        log.info("Generating summary tables for: {}", cls.shortname)

        # Table
        summarytable = cls.get_standard_summary_table_name()
        pkfieldname = table + "_pk"
        dummy_instance = cls(None)  # blank PK
        fieldspecs = [
            dict(name=pkfieldname, cctype="INT_UNSIGNED", notnull=True,
                 comment="(GENERIC) FK to the source table's _pk field"),
            dict(name="when_source_record_created_utc",
                 cctype="DATETIME",
                 comment="(GENERIC) When was the source record created?"),
            dict(name="when_summary_created_utc", cctype="DATETIME",
                 comment="(GENERIC) When was this summary created?"),
            dict(name="seconds_from_creation_to_first_finish",
                 cctype="FLOAT",
                 comment="(GENERIC) Time (in seconds) from record creation to "
                         "first exit, if that was a finish not an abort")
        ] + dummy_instance.get_summaries(req)
        cc_db.add_sqltype_to_fieldspeclist_in_place(fieldspecs)
        fields = [d["name"] for d in fieldspecs]
        pls.db.make_table(summarytable, fieldspecs, dynamic=True)
        for i in cls.gen_all_current_tasks():
            # noinspection PyProtectedMember
            values = [
                i._pk,  # tablename_pk
                i.get_creation_datetime_utc(),
                # ... when_source_record_created_utc
                now,  # when_summary_created_utc
                i.get_seconds_from_creation_to_first_finish()
                # ... seconds_from_creation_to_first_finish
            ] + [
                s["value"] for s in i.get_summaries(req)
            ]
            pls.db.insert_record(summarytable, fields, values)
        # All records are current (see generator above).
        # For non-anonymous tasks, we can add patient information:
        if not cls.is_anonymous:
            cc_db.create_summary_table_current_view_withpt(summarytable, table,
                                                           pkfieldname)

    @classmethod
    def make_extra_summary_tables(cls, now: datetime.datetime) -> None:
        # Get details of what the task wants
        infolist = list(cls.extra_summary_table_info)
        # ... copy; one entry per table
        # Make simple fieldnames from fieldspecs
        for i in range(len(infolist)):
            infolist[i]["fields"] = [fs["name"]
                                     for fs in infolist[i]["fieldspecs"]]
        # Make tables
        for i in range(len(infolist)):
            summarytable = infolist[i]["tablename"]
            fieldspecs = infolist[i]["fieldspecs"]
            cc_db.add_sqltype_to_fieldspeclist_in_place(fieldspecs)
            pls.db.make_table(summarytable, fieldspecs, dynamic=True)
        # Populate tables
        for task in cls.gen_all_current_tasks():
            datalist = task.get_extra_summary_table_data(now)
            for i in range(len(infolist)):
                summarytable = infolist[i]["tablename"]
                fields = infolist[i]["fields"]
                rows_to_insert = datalist[i]
                pls.db.insert_multiple_records(summarytable, fields,
                                               rows_to_insert)
        # All records are current (see generator above).
        # Make views:
        if not cls.is_anonymous:
            for i in range(len(infolist)):
                basetable = cls.tablename
                summarytable = infolist[i]["tablename"]
                pkfieldname = infolist[i]["fields"][0]
                cc_db.create_summary_table_current_view_withpt(summarytable,
                                                               basetable,
                                                               pkfieldname)

    def is_complete_summary_field(self) -> SummaryElement:
        return SummaryElement(name="is_complete",
                              coltype=Boolean(),
                              value=self.is_complete(),
                              comment=COMMENT_IS_COMPLETE)

    def get_summary_names(self, req: CamcopsRequest) -> List[str]:
        """
        Returns a list of summary field names.
        """
        return [x.name for x in self.get_summaries(req)]

    # -------------------------------------------------------------------------
    # More on tables
    # -------------------------------------------------------------------------

    @classmethod
    def get_all_table_and_view_names(cls) -> Tuple[List[str], List[str]]:
        """Returns a tuple (tables, views) with lists of all tables and views
        used by this task."""
        basetablename = cls.tablename
        tables = [basetablename]
        views = [basetablename + "_current"]
        if not cls.is_anonymous:
            views.append(basetablename + "_current_withpt")

        extratables = cls.get_extra_table_names()
        for et in extratables:
            tables.append(et)
            views.append(et + "_current")

        summarytable = cls.get_standard_summary_table_name()
        tables.append(summarytable)
        if not cls.is_anonymous:
            views.append(summarytable + "_current")
            # ... includes patient info too
            views.append(summarytable + "_current_withpt")

        extrasummarytables = cls.get_extra_summary_table_names()
        for est in extrasummarytables:
            tables.append(est)
            if not cls.is_anonymous:
                views.append(est + "_current")
                # ... includes patient info too
                views.append(est + "_current_withpt")

        return tables, views

    @classmethod
    def get_extra_summary_table_names(cls) -> List[str]:
        return [x["tablename"] for x in cls.extra_summary_table_info]

    # -------------------------------------------------------------------------
    # BLOB fetching
    # -------------------------------------------------------------------------

    def get_blob_by_id(self, blobid: int) -> Optional[Blob]:
        """Get Blob() object from blob ID, or None."""
        return get_blob_by_id(self, blobid)

    # -------------------------------------------------------------------------
    # Testing
    # -------------------------------------------------------------------------

    def dump(self) -> None:
        """Dump to log."""
        line_equals = "=" * 79
        lines = ["", line_equals]
        for f in self.get_fieldnames():
            lines.append("{f}: {v!r}".format(f=f, v=getattr(self, f)))
        lines.append(line_equals)
        log.info("\n".join(lines))

    # -------------------------------------------------------------------------
    # Special notes
    # -------------------------------------------------------------------------

    def apply_special_note(self,
                           req: CamcopsRequest,
                           note: str,
                           user_id: int,
                           from_console: bool = False) -> None:
        """Manually applies a special note to a task.

        Applies it to all predecessor/successor versions as well.
        WRITES TO DATABASE.
        """
        # *** needs fixing
        sn = SpecialNote()
        sn.basetable = self.tablename
        sn.task_id = self.id
        sn.device_id = self._device_id
        sn.era = self._era
        sn.note_at = format_datetime(pls.NOW_LOCAL_TZ, DATEFORMAT.ISO8601)
        sn.user_id = user_id
        sn.note = note
        sn.save()
        self.audit(req, "Special note applied manually", from_console)
        self.delete_from_hl7_message_log(from_console)

    # -------------------------------------------------------------------------
    # Clinician
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_clinician_name(self) -> str:
        """
        Get the clinician's name.
        May be overridden by TaskHasClinicianMixin.
        """
        return ""

    # -------------------------------------------------------------------------
    # Respondent
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def is_respondent_complete(self) -> bool:
        """
        May be overridden by TaskHasRespondentMixin.
        """
        return False

    # -------------------------------------------------------------------------
    # About the associated patient
    # -------------------------------------------------------------------------

    @property
    def patient(self) -> Optional[Patient]:
        """
        Overridden by TaskHasPatientMixin.
        """
        return None

    def is_female(self) -> bool:
        """Is the patient female?"""
        return self.patient.is_female() if self.patient else False

    def is_male(self) -> bool:
        """Is the patient male?"""
        return self.patient.is_male() if self.patient else False

    def get_patient_server_pk(self) -> Optional[int]:
        """Get the server PK of the patient, or None."""
        if self.is_anonymous:
            return None
        return self.patient.get_pk()

    def get_patient(self) -> Optional[Patient]:
        """Get the associated Patient() object."""
        log.critical("Deprecated; remove")
        return self.patient

    def get_patient_forename(self) -> str:
        """Get the patient's forename, in upper case, or ""."""
        return self.patient.get_forename() if self.patient else ""

    def get_patient_surname(self) -> str:
        """Get the patient's surname, in upper case, or ""."""
        return self.patient.get_surname() if self.patient else ""

    def get_patient_dob(self) -> Optional[datetime.date]:
        """Get the patient's DOB, or None."""
        return self.patient.get_surname() if self.patient else None

    def get_patient_dob_first11chars(self) -> Optional[str]:
        """For example: '29 Dec 1999'."""
        if not self.patient:
            return None
        dob_str = self.patient.get_dob_str()
        if not dob_str:
            return None
        return dob_str[:11]

    def get_patient_sex(self) -> str:
        """Get the patient's sex, or ""."""
        return self.patient.get_sex() if self.patient else ""

    def get_patient_address(self) -> str:
        """Get the patient's address, or ""."""
        return self.patient.get_address() if self.patient else ""

    def get_patient_idnum_objects(self) -> List[PatientIdNum]:
        return self.patient.get_idnum_objects() if self.patient else []

    def get_patient_idnum_object(self,
                                 which_idnum: int) -> Optional[PatientIdNum]:
        """
        Get the patient's ID number, or None.
        """
        return (self.patient.get_idnum_object(which_idnum) if self.patient
                else None)

    def get_patient_idnum_value(self, which_idnum: int) -> Optional[int]:
        idobj = self.get_patient_idnum_object(which_idnum=which_idnum)
        return idobj.idnum_value if idobj else None

    def get_patient_hl7_pid_segment(self,
                                    recipient_def: RecipientDefinition) \
            -> Union[hl7.Segment, str]:
        """Get patient HL7 PID segment, or ""."""
        return (self.patient.get_hl7_pid_segment(recipient_def) if self.patient
                else "")

    # -------------------------------------------------------------------------
    # HL7
    # -------------------------------------------------------------------------

    def get_hl7_data_segments(self, recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        """Returns a list of HL7 data segments.

        These will be:
            OBR segment
            OBX segment
            any extra ones offered by the task
        """
        obr_segment = make_obr_segment(self)
        obx_segment = make_obx_segment(
            self,
            task_format=recipient_def.task_format,
            observation_identifier=self.tablename + "_" + str(self._pk),
            observation_datetime=self.get_creation_datetime(),
            responsible_observer=self.get_clinician_name(),
            xml_field_comments=recipient_def.xml_field_comments
        )
        return [
            obr_segment,
            obx_segment
        ] + self.get_hl7_extra_data_segments(recipient_def)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_hl7_extra_data_segments(self, recipient_def: RecipientDefinition) \
            -> List[hl7.Segment]:
        """Return a list of any extra HL7 data segments.

        May be overridden.
        """
        return []

    def delete_from_hl7_message_log(self, from_console: bool = False) -> None:
        """Erases the object from the HL7 message log (so it will be resent).
        """
        if self._pk is None:
            return
        sql = """
            UPDATE  {}
            SET     cancelled = 1,
                    cancelled_at_utc = ?
            WHERE   basetable = ?
            AND     serverpk = ?
            AND     (NOT cancelled OR cancelled IS NULL)
        """.format(
            HL7MESSAGE_TABLENAME,
            self._pk
        )
        args = [
            pls.NOW_UTC_NO_TZ,
            self.tablename,
            self._pk,
        ]
        pls.db.db_exec(sql, *args)
        self.audit(
            req,
            "Task cancelled in outbound HL7 message log (may trigger "
            "resending)",
            from_console
        )

    # -------------------------------------------------------------------------
    # Audit
    # -------------------------------------------------------------------------

    def audit(self, req: CamcopsRequest, details: str,
              from_console: bool = False) -> None:
        """Audits actions to this task."""
        audit(req,
              details,
              patient_server_pk=self.get_patient_server_pk(),
              table=self.tablename,
              server_pk=self._pk,
              from_console=from_console)

    # -------------------------------------------------------------------------
    # Erasure (wiping, leaving record as placeholder)
    # -------------------------------------------------------------------------

    def manually_erase(self, req: CamcopsRequest, user_id: int) -> None:
        """Manually erases a task (including sub-tables).
        Also erases linked non-current records.
        This WIPES THE CONTENTS but LEAVES THE RECORD AS A PLACEHOLDER.

        Audits the erasure. Propagates erase through to the HL7 log, so those
        records will be re-sent. WRITES TO DATABASE.
        """
        if self._pk is None or self._era == ERA_NOW:
            return

        # 1. Erase subtable records
        self.erase_subtable_records_even_noncurrent(user_id)
        # ... running that for each task would just duplicate DELETE calls

        # 2. Erase BLOBs
        blob_pks = self.get_blob_pks_of_record_group()
        for bpk in blob_pks:
            blob = Blob(bpk)
            cc_db.manually_erase_record_object_and_save(
                blob, Blob.TABLENAME, Blob.FIELDS, user_id)

        # 3. Erase tasks
        tablename = self.tablename
        fields = self.get_fields()
        pklist = self.get_server_pks_of_record_group()
        for pk in pklist:
            task = task_factory(tablename, pk)
            cc_db.manually_erase_record_object_and_save(task, tablename,
                                                        fields, user_id)

        # 4. Audit and clear HL7 message log
        self.audit(req, "Task details erased manually")
        self.delete_from_hl7_message_log()

    def get_server_pks_of_record_group(self) -> List[int]:
        """Returns server PKs of all records that represent versions of this
        one."""
        return cc_db.get_server_pks_of_record_group(
            self.tablename,
            PKNAME,
            "id",
            self.id,
            self._device_id,
            self._era
        )

    def is_erased(self) -> bool:
        return self._manually_erased

    def erase_subtable_records_even_noncurrent(self, user_id: int) -> None:
        """Override to erase contents of subtable records that are linked to
        this record, and save to database.

        Usually, done with DELETE FROM subtable WHERE fk = self.id AND ...

        See manually_erase().
        """
        for depclass in self.dependent_classes:
            tablename = depclass.tablename
            fieldspecs = depclass.get_full_fieldspecs()
            fkname = depclass.fkname
            fieldnames = [f["name"] for f in fieldspecs]
            cc_db.erase_subtable_records_common(
                depclass, tablename, fieldnames, PKNAME,
                fkname, self.id, self._device_id, self._era,
                user_id)

    # -------------------------------------------------------------------------
    # Complete deletion
    # -------------------------------------------------------------------------

    @classmethod
    def get_task_pks_wc_for_patient_deletion(
            cls,
            which_idnum: int,
            idnum_value: int) -> Sequence[Tuple[int, datetime.datetime]]:
        if cls.is_anonymous:
            return []
        table = cls.tablename
        wcfield_utc = cls.whencreated_fieldexpr_as_utc()
        query = """
            SELECT {table}._pk, {wcfield_utc}
            FROM {table}
            INNER JOIN patient
                ON {table}.patient_id = patient.id
                AND {table}._device_id = patient._device_id
                AND {table}._era = patient._era
            WHERE
                patient.idnum{which_idnum} = ?
        """.format(
            table=table,
            wcfield_utc=wcfield_utc,
            which_idnum=which_idnum,
        )
        args = [idnum_value]
        return pls.db.fetchall(query, *args)

    @classmethod
    def get_task_pks_for_patient_deletion(cls,
                                          which_idnum: int,
                                          idnum_value: int) -> Sequence[int]:
        pk_wc = cls.get_task_pks_wc_for_patient_deletion(which_idnum,
                                                         idnum_value)
        return [row[0] for row in pk_wc]

    def delete_entirely(self, req: CamcopsRequest) -> None:
        if self._pk is None:
            return

        # 1. Get rid of subtable records
        self.delete_subtable_records_even_noncurrent()
        # ... running that for each task would just duplicate DELETE calls

        # 2. Get rid of BLOBs
        blob_pks = self.get_blob_pks_of_record_group()
        cc_db.delete_from_table_by_pklist(Blob.TABLENAME,
                                          PKNAME, blob_pks)

        # 3. Get rid of tasks
        tablename = self.tablename
        taskpks = self.get_server_pks_of_record_group()
        cc_db.delete_from_table_by_pklist(tablename, PKNAME, taskpks)

        # 4. Audit
        audit(req,
              "Task deleted",
              patient_server_pk=self.get_patient_server_pk(),
              table=tablename,
              server_pk=self._pk)

    def delete_subtable_records_even_noncurrent(self) -> None:
        """Override to DELETE subtable records from the database that are
        linked to this record (even non-current, historical ones).

        Used for whole-patient deletion.
        See delete_entirely().
        """
        for depclass in self.dependent_classes:
            tablename = depclass.tablename
            fkname = depclass.fkname
            cc_db.delete_subtable_records_common(
                tablename, PKNAME,
                fkname, self.id, self._device_id, self._era)

    def get_blob_ids(self) -> List[int]:
        blob_fields = self.get_blob_fields()
        blob_ids = [getattr(self, f) for f in blob_fields]
        blob_ids = [x for x in blob_ids if x is not None]
        return blob_ids

    def get_blob_pks_of_record_group(self) -> List[int]:
        tablename = self.tablename
        taskpks = self.get_server_pks_of_record_group()
        tasks = [task_factory(tablename, pk) for pk in taskpks]
        list_of_blob_id_lists = [t.get_blob_ids() for t in tasks]
        blob_ids = flatten_list(list_of_blob_id_lists)
        blob_ids = list(set(blob_ids))  # remove duplicates
        list_of_blob_pk_lists = [
            cc_db.get_server_pks_of_record_group(
                Blob.TABLENAME, PKNAME, "id", i,
                self._device_id, self._era)
            for i in blob_ids]
        blob_pks = flatten_list(list_of_blob_pk_lists)
        blob_pks = list(set(blob_pks))
        return blob_pks

    # -------------------------------------------------------------------------
    # Viewing the task in the list of tasks
    # -------------------------------------------------------------------------

    def is_live_on_tablet(self) -> bool:
        """Is the instance live on a tablet?"""
        return self._era == ERA_NOW

    def get_task_list_row(self, req: CamcopsRequest) -> str:
        """HTML table row for including in task summary list."""
        complete = self.is_complete()
        anonymous = self.is_anonymous
        if anonymous:
            patient_id = "—"
        else:
            patient_id = self.patient.get_html_for_webview_patient_column(req)
        satisfies_upload = (
            anonymous or self.patient.satisfies_upload_id_policy()
        )
        satisfies_finalize = (
            anonymous or self.patient.satisfies_finalize_id_policy()
        )
        # device = Device(self._device_id)
        live_on_tablet = self.is_live_on_tablet()

        if anonymous:
            # conflict = False
            idmsg = "—"
        else:
            # conflict, idmsg = self.patient.get_conflict_html_for_id_col()
            idmsg = self.patient.get_html_for_id_col(req)

        if satisfies_upload and satisfies_finalize:
            colour_policy = ''
        elif not satisfies_upload:
            colour_policy = ' class="badidpolicy_severe"'
        else:
            colour_policy = ' class="badidpolicy_mild"'

        return """
            <tr>
                <td{colour_policy}>{patient_id}</td>
                <td>{idmsg}</td>
                <td{colour_not_current}><b>{tasktype}</b></td>
                <td>{adding_user}</td>
                <td{colour_live}>{created}</td>
                <td{colour_incomplete}>{html}</td>
                <td{colour_incomplete}>{pdf}</td>
            </tr>
        """.format(
            colour_policy=colour_policy,
            patient_id=patient_id,
            # colour_conflict=' class="warning"' if conflict else '',
            idmsg=idmsg,
            colour_not_current=' class="warning"' if not self._current else '',
            tasktype=self.shortname,
            adding_user=self.get_adding_user_username(),
            colour_live=' class="live_on_tablet"' if live_on_tablet else '',
            created=format_datetime_string(self.when_created,
                                           DATEFORMAT.SHORT_DATETIME),
            colour_incomplete='' if complete else ' class="incomplete"',
            html=self.get_hyperlink_html(req, "HTML"),
            pdf=self.get_hyperlink_pdf(req, "PDF"),
        )
        # Note: target="_blank" is deprecated, but preferred by users (it
        # obviates the need to manually confirm refresh of the view-tasks page,
        # which is generated following a POST submission).

    # -------------------------------------------------------------------------
    # Fetching and filtering tasks for the task list
    # -------------------------------------------------------------------------

    def allowed_to_user(self, session: 'CamcopsSession') -> bool:
        """Is the current user allowed to see this task?"""
        if (session.restricted_to_viewing_user() is not None and
                session.restricted_to_viewing_user() != self._adding_user):
            return False
        return True

    @classmethod
    def filter_allows_task_type(cls, session: 'CamcopsSession') -> bool:
        return (session.filter_task is None or
                session.filter_task == cls.tablename)

    def is_compatible_with_filter(self, session: 'CamcopsSession') -> bool:
        """Is this task allowed through the filter?"""
        # 1. Quick things
        if not self.allowed_to_user(session):
            return False
        if (session.filter_device_id is not None and
                session.filter_device_id != self._device_id):
            return False
        if (session.filter_user_id is not None and
                session.filter_user_id != self._adding_user_id):
            return False
        if (session.filter_task is not None and
                session.filter_task != self.tablename):
            return False
        start_datetime = session.get_filter_start_datetime()
        end_datetime = session.get_filter_end_datetime_corrected_1day()
        task_datetime = self.get_creation_datetime()
        if start_datetime is not None and task_datetime < start_datetime:
            return False
        if end_datetime is not None and task_datetime > end_datetime:
            return False

        # 2. Medium-speed things
        if (session.filter_complete is not None and
                session.filter_complete != self.is_complete()):
            return False

        # 3. Since we've already loaded patient info, not slow:
        if session.filter_surname is not None:
            if self.patient.surname is None:
                return False
            temp_pt_surname = self.patient.surname.upper()
            if session.filter_surname.upper() != temp_pt_surname:
                return False
        if session.filter_forename is not None:
            if self.patient.forename is None:
                return False
            temp_pt_forename = self.patient.forename.upper()
            if session.filter_forename.upper() != temp_pt_forename:
                return False
        if session.filter_dob_iso8601 is not None:
            if self.patient.dob != session.filter_dob_iso8601:
                return False
        if session.filter_sex is not None:
            if self.patient.sex is None:
                return False
            temp_pt_sex = self.patient.sex.upper()
            if session.filter_sex.upper() != temp_pt_sex:
                return False
        for which_idnum, idnum_value in session.get_idnum_filters():
            if (idnum_value is not None and
                    idnum_value != self.patient.get_idnum_value(which_idnum)):
                return False

        # 4. Slow:
        if session.filter_text is not None:
            if not self.compatible_with_text_filter(session.filter_text):
                return False
        return True

    def compatible_with_text_filter(self, filtertext: str) -> bool:
        """
        Is this task allowed through the text contents filter?
        Does one of its text fields contain the filtertext?

        (Searches all text fields, ignoring "administrative" ones.)
        """
        filtertext = filtertext.upper()
        for attrname, column in gen_columns(self):
            if attrname in TEXT_FILTER_EXEMPT_FIELDS:
                continue
            if not is_sqlatype_string(column.type):
                continue
            value = getattr(self, attrname)
            if not isinstance(value, str):
                # handles None and anything unexpectedly odd
                continue
            if filtertext in value.upper():
                return True
        return False

    # -------------------------------------------------------------------------
    # Fetching tasks for trackers/CTVs
    # -------------------------------------------------------------------------

    @classmethod
    def get_task_pks_for_tracker(
            cls,
            idnum_criteria: List[Tuple[int, int]],  # which_idnum, idnum_value
            start_datetime: Optional[datetime.datetime],
            end_datetime: Optional[datetime.datetime]) -> List[int]:
        """Get server PKs for tracker information matching the requested
        criteria, or []."""
        if not cls.provides_trackers:
            return []
        return cls.get_task_pks_for_tracker_or_clinical_text_view(
            idnum_criteria, start_datetime, end_datetime)

    @classmethod
    def get_task_pks_for_clinical_text_view(
            cls,
            idnum_criteria: List[Tuple[int, int]],  # which_idnum, idnum_value
            start_datetime: Optional[datetime.datetime],
            end_datetime: Optional[datetime.datetime]) -> List[int]:
        """Get server PKs for CTV information matching the requested criteria,
        or []."""
        # Return ALL tasks (those not providing clinical text appear as
        # hypertext headings)
        return cls.get_task_pks_for_tracker_or_clinical_text_view(
            idnum_criteria, start_datetime, end_datetime)

    @classmethod
    def get_task_pks_for_tracker_or_clinical_text_view(
            cls,
            idnum_criteria: List[Tuple[int, int]],  # which_idnum, idnum_value
            start_datetime: Optional[datetime.datetime],
            end_datetime: Optional[datetime.datetime]) -> List[int]:
        """Get server PKs matching requested criteria.

        Args:
            idnum_criteria: List of tuples of (which_idnum, idnum_value) to
                restrict to
            start_datetime: earliest date, or None
            end_datetime: latest date, or None

        Must not be called for anonymous tasks.
        """
        if not idnum_criteria:
            return []
        table = cls.tablename
        # We don't do trackers/clinical_text_view for anonymous tasks
        # (nonsensical), so this is always OK:
        query = """
            SELECT t._pk
            FROM {tasktable} t
            INNER JOIN {patienttable} p
                ON t.patient_id = p.id
                AND t._device_id = p._device_id
                AND t._era = p._era
            INNER JOIN {idtable} i
                ON i.patient_id = p.id
                AND i._device_id = p._device_id
                AND i._era = p._era
            WHERE
                t._current
                AND p._current
                AND i._current
        """.format(
            tasktable=table,
            patienttable=Patient.TABLENAME,
            idtable=PatientIdNum.tablename,
        )
        wheres = []
        args = []
        for which_idnum, idnum_value in idnum_criteria:
            if which_idnum is None or idnum_value is None:
                continue
            wheres.append("i.which_idnum = ?")
            args.append(which_idnum)
            wheres.append("i.idnum_value = ?")
            args.append(idnum_value)
        wcfield_utc = cls.whencreated_fieldexpr_as_utc(table_alias='t')
        if start_datetime is not None:
            wheres.append("{} >= ?".format(wcfield_utc))
            args.append(start_datetime)
        if end_datetime is not None:
            wheres.append("{} <= ?".format(wcfield_utc))
            args.append(end_datetime)
        if wheres:
            query += " AND " + " AND ".join(wheres)
        return pls.db.fetchallfirstvalues(query, *args)

    # -------------------------------------------------------------------------
    # Generators for the basic research dump
    # -------------------------------------------------------------------------

    @classmethod
    def get_all_current_pks(
            cls,
            start_datetime: datetime.datetime = None,
            end_datetime: datetime.datetime = None,
            sort: bool = False,
            reverse: bool = False) -> List[int]:
        """Returns PKs for all current tasks, optionally within the specified
        date range."""
        table = cls.tablename
        query = """
            SELECT _pk
            FROM {}
            WHERE _current
        """.format(table)
        wheres = []
        args = []
        wcfield_utc = cls.whencreated_fieldexpr_as_utc()
        if start_datetime is not None:
            wheres.append("{} >= ?".format(wcfield_utc))
            args.append(start_datetime)
        if end_datetime is not None:
            wheres.append("{} <= ?".format(wcfield_utc))
            args.append(end_datetime)
        if wheres:
            query += " AND " + " AND ".join(wheres)
        if sort:
            query += " ORDER BY " + wcfield_utc
            if reverse:
                query += " DESC"
        return pls.db.fetchallfirstvalues(query, *args)

    @classmethod
    def gen_all_current_tasks(
            cls,
            start_datetime: datetime.datetime = None,
            end_datetime: datetime.datetime = None,
            sort: bool = False,
            reverse: bool = False) -> Generator[TASK_FWD_REF, None, None]:
        """Gets all tasks that are current within the specified date range.
        Either date may be None."""
        pks = cls.get_all_current_pks(start_datetime, end_datetime,
                                      sort=sort, reverse=reverse)
        for pk in pks:
            yield cls(pk)
        # *** CHANGE THIS: inefficient; runs multiple queries where one would do

    @classmethod
    def gen_all_tasks_matching_session_filter(
            cls,
            session: 'CamcopsSession',
            sort: bool = False,
            reverse: bool = False) -> Generator[TASK_FWD_REF, None, None]:
        if not cls.filter_allows_task_type(session):
            return
            # http://stackoverflow.com/questions/13243766
        pk_wc = cls.get_session_candidate_task_pks_whencreated(
            session, sort=sort, reverse=reverse)
        # Yield those that really do match the filter
        for pk, wc in pk_wc:
            task = cls(pk)
            if task is not None and task.is_compatible_with_filter(session):
                yield task
        # *** CHANGE THIS: inefficient; runs multiple queries where one would do

    # -------------------------------------------------------------------------
    # TSV export for basic research dump
    # -------------------------------------------------------------------------

    def get_dictlist_for_tsv(self, req: CamcopsRequest) -> List[Dict]:
        """Returns information for the basic research dump in TSV format.

        Returns
            l
        where
            l is a list of d;
                d is a dictionary with keys:
                    "filenamestem": filename stem (to which ".tsv" will be
                        appended)
                    "rows": list of OrderedDict that represent the TSV content
                        for this task instance.
        """

        # Validity checking: can't have two keys the same in a dictionary,
        # so we can't have a conflict.

        mainrow = collections.OrderedDict(
            (f, getattr(self, f)) for f in self.get_fields())
        if self.patient:
            mainrow.update(self.patient.get_dict_for_tsv(req))
        mainrow.update(collections.OrderedDict(
            (s["name"], s["value"]) for s in self.get_summaries(req)))
        maindict = {
            "filenamestem": self.tablename,
            "rows": [mainrow]
        }
        return [maindict] + self.get_extra_dictlist_for_tsv()

    def get_extra_dictlist_for_tsv(self) -> List[Dict]:
        """Override for tasks with subtables to be encoded as separate files
        in the TSV output.

        Same return format at get_dictlist_for_tsv (q.v.)
        """
        dictlist = []
        for depclass in self.dependent_classes:
            dictlist.append(self.get_extra_dict_for_tsv(
                subtable=depclass.tablename,
                fields=depclass.get_fieldnames(),
                items=self.get_ancillary_items(depclass)
            ))
        return dictlist

    def get_extra_dict_for_tsv(self,
                               subtable: str,
                               fields: Iterable[str],
                               items: Iterable[Any]) -> Dict:
        maintable = self.tablename
        mainpk = self._pk
        rows = []
        for i in items:
            d = collections.OrderedDict({"_" + maintable + "_pk": mainpk})
            for f in fields:
                d[f] = getattr(i, f)
            rows.append(d)
        return {
            "filenamestem": subtable,
            "rows": rows
        }

    # -------------------------------------------------------------------------
    # Data structure for CRIS data dictionary
    # -------------------------------------------------------------------------

    @classmethod
    def get_cris_dd_rows(cls, req: CamcopsRequest) -> List[Dict]:
        if cls.is_anonymous:
            return []
        taskname = cls.shortname
        tablename = CRIS_TABLENAME_PREFIX + cls.tablename
        instance = cls(None)  # blank PK
        common = instance.get_cris_common_fieldspecs_values()
        taskfieldspecs = instance.get_cris_fieldspecs_values(req, common)
        rows = get_cris_dd_rows_from_fieldspecs(taskname, tablename,
                                                taskfieldspecs)
        for depclass in cls.dependent_classes:
            depinstance = depclass(None)  # blank PK
            deptable = CRIS_TABLENAME_PREFIX + depinstance.tablename
            depfieldspecs = depinstance.get_cris_fieldspecs_values(req, common)
            rows += get_cris_dd_rows_from_fieldspecs(taskname, deptable,
                                                     depfieldspecs)
        return rows

    # -------------------------------------------------------------------------
    # Data export for CRIS and other anonymisation systems
    # -------------------------------------------------------------------------

    @classmethod
    def make_cris_tables(cls, req: CamcopsRequest,
                         db: DatabaseSupporter) -> None:
        # DO NOT CONFUSE pls.db and db. HERE WE ONLY USE db.
        log.info("Generating CRIS staging tables for: {}", cls.shortname)
        cc_db.set_db_to_utf8(db)
        task_table = CRIS_TABLENAME_PREFIX + cls.tablename
        created_tables = []
        for task in cls.gen_all_current_tasks():
            common_fsv = task.get_cris_common_fieldspecs_values()
            task_fsv = task.get_cris_fieldspecs_values(req, common_fsv)
            cc_db.add_sqltype_to_fieldspeclist_in_place(task_fsv)
            if task_table not in created_tables:
                db.drop_table(task_table)
                db.make_table(task_table, task_fsv, dynamic=True)
                created_tables.append(task_table)
            db.insert_record_by_fieldspecs_with_values(task_table, task_fsv)
            # Same for associated ancillary items
            for depclass in cls.dependent_classes:
                items = task.get_ancillary_items(depclass)
                for it in items:
                    item_table = CRIS_TABLENAME_PREFIX + it.tablename
                    item_fsv = it.get_cris_fieldspecs_values(common_fsv)
                    cc_db.add_sqltype_to_fieldspeclist_in_place(item_fsv)
                    if item_table not in created_tables:
                        db.drop_table(item_table)
                        db.make_table(item_table, item_fsv, dynamic=True)
                        created_tables.append(item_table)
                    db.insert_record_by_fieldspecs_with_values(item_table,
                                                               item_fsv)

    def get_cris_common_fieldspecs_values(self) -> FIELDSPECLIST_TYPE:
        # Store the task's PK in its own but all linked records
        clusterpk_fs = copy.deepcopy(CRIS_CLUSTER_KEY_FIELDSPEC)
        clusterpk_fs["value"] = self._pk
        fieldspecs = [clusterpk_fs]
        # Store a subset of patient info in all linked records
        patientfs = copy.deepcopy(Patient.FIELDSPECS)
        for fs in patientfs:
            if fs.get("cris_include", False):
                fs["value"] = getattr(self.patient, fs["name"])
                fs["name"] = TSV_PATIENT_FIELD_PREFIX + fs["name"]
                fs["comment"] = CRIS_PATIENT_COMMENT_PREFIX + fs.get("comment",
                                                                     "")
                fieldspecs.append(fs)
        return fieldspecs

    def get_cris_fieldspecs_values(
            self,
            req: CamcopsRequest,
            common_fsv: FIELDSPECLIST_TYPE) -> FIELDSPECLIST_TYPE:
        fieldspecs = copy.deepcopy(self.get_full_fieldspecs())
        for fs in fieldspecs:
            fs["value"] = getattr(self, fs["name"])
        summaries = self.get_summaries(req)  # summaries include values
        for fs in summaries:
            fs["comment"] = CRIS_SUMMARY_COMMENT_PREFIX + fs.get("comment", "")
        return (
            common_fsv +
            fieldspecs +
            summaries
        )

    # -------------------------------------------------------------------------
    # XML view
    # -------------------------------------------------------------------------

    def get_xml(self,
                req: CamcopsRequest,
                include_calculated: bool = True,
                include_blobs: bool = True,
                include_patient: bool = True,
                indent_spaces: int = 4,
                eol: str = '\n',
                skip_fields: List[str] = None,
                include_comments: bool = False) -> str:
        """Returns XML UTF-8 document representing task."""
        skip_fields = skip_fields or []
        tree = self.get_xml_root(req=req,
                                 include_calculated=include_calculated,
                                 include_blobs=include_blobs,
                                 include_patient=include_patient,
                                 skip_fields=skip_fields)
        return get_xml_document(
            tree,
            indent_spaces=indent_spaces,
            eol=eol,
            include_comments=include_comments
        )

    def get_xml_root(self,
                     req: CamcopsRequest,
                     include_calculated: bool = True,
                     include_blobs: bool = True,
                     include_patient: bool = True,
                     skip_fields: List[str] =None) -> XmlElement:
        """Returns XML tree. Return value is the root XmlElementTuple.

        Override to include other tables, or to deal with BLOBs, if the default
        methods are insufficient.
        """
        skip_fields = skip_fields or []

        # Core (inc. core BLOBs)
        branches = self.get_xml_core_branches(
            req=req,
            include_calculated=include_calculated,
            include_blobs=include_blobs,
            include_patient=include_patient,
            skip_fields=skip_fields)
        # Dependent classes/tables
        depclasslist = self.dependent_classes
        for depclass in depclasslist:
            tablename = depclass.tablename
            fieldspecs = depclass.get_full_fieldspecs()
            itembranches = []
            items = self.get_ancillary_items(depclass)
            if items:
                blobinfo = get_camcops_blob_column_attr_names(items[0])
                for it in items:
                    # Simple fields for ancillary items
                    itembranches.append(XmlElement(
                        name=tablename,
                        value=make_xml_branches_from_fieldspecs(
                            it,
                            skip_fields=skip_fields)
                    ))
                    # BLOBs for ancillary items
                    if include_blobs and blobinfo:
                        itembranches.append(XML_COMMENT_BLOBS)
                        itembranches.extend(
                            it.make_xml_branches_for_blob_fields(
                                skip_fields=skip_fields))
            branches.append("<!-- Items for {} -->\n".format(tablename))
            branches.append(XmlElement(
                name=tablename,
                value=itembranches
            ))
        tree = XmlElement(name=self.tablename, value=branches)
        return tree

    def get_xml_core_branches(
            self,
            req: CamcopsRequest,
            include_calculated: bool = True,
            include_blobs: bool = True,
            include_patient: bool = True,
            skip_fields: List[str] = None) -> List[XmlElement]:
        """Returns a list of XmlElementTuple elements representing stored,
        calculated, patient, and/or BLOB fields, depending on the options."""
        skip_fields = skip_fields or []
        # Stored
        branches = [XML_COMMENT_STORED]
        branches.extend(make_xml_branches_from_fieldspecs(
            self, skip_fields=skip_fields))
        # Special notes
        branches.append(XML_COMMENT_SPECIAL_NOTES)
        for sn in self.special_notes:
            branches.append(sn.get_xml_root())
        # Calculated
        if include_calculated:
            branches.append(XML_COMMENT_CALCULATED)
            branches.extend(make_xml_branches_from_summaries(
                self.get_summaries(req), skip_fields=skip_fields))
        # Patient details
        if self.is_anonymous:
            branches.append(XML_COMMENT_ANONYMOUS)
        elif include_patient:
            branches.append(XML_COMMENT_PATIENT)
            if self.patient:
                branches.append(self.patient.get_xml_root(req))
        # BLOBs
        blobinfo = self.blob_name_idfield_list
        if include_blobs and blobinfo:
            branches.append(XML_COMMENT_BLOBS)
            branches.extend(self.make_xml_branches_for_blob_fields(
                skip_fields=skip_fields))
        return branches

    def make_xml_branches_for_blob_fields(
            self,
            skip_fields: List[str] = None) -> List[XmlElement]:
        """Returns list of XmlElementTuple elements for BLOB fields."""
        skip_fields = skip_fields or []
        return make_xml_branches_for_blob_fields(self, skip_fields=skip_fields)

    def get_blob_xml_tuple(self,
                           blobid: int,
                           name: str) -> XmlElement:
        """Get XmlElementTuple for a PNG BLOB."""
        return get_blob_xml_tuple(self, blobid, name)

    # -------------------------------------------------------------------------
    # HTML view
    # -------------------------------------------------------------------------

    def get_core_html(self, req: CamcopsRequest) -> str:
        html = ""
        if self.has_clinician:
            html += self.get_standard_clinician_block()
        if self.has_respondent:
            html += self.get_standard_respondent_block()
        html += self.get_task_html(req)
        return html

    def get_html(self, req: CamcopsRequest, anonymise: bool = False) -> str:
        """Returns HTML representing task."""
        cfg = req.config
        set_matplotlib_fontsize(cfg.PLOT_FONTSIZE)
        req.switch_output_to_svg()
        return render("task.mako",
                      dict(task=self,
                           anonymise=anonymise,
                           viewtype=ViewArg.HTML),
                      request=req)

    def get_hyperlink_html(self, req: CamcopsRequest, text: str) -> str:
        """Hyperlink to HTML version."""
        return """<a href="{}" target="_blank">{}</a>""".format(
            get_url_task_html(req, self.tablename, self._pk),
            text
        )

    # -------------------------------------------------------------------------
    # PDF view
    # -------------------------------------------------------------------------

    def get_pdf(self, req: CamcopsRequest) -> bytes:
        """Returns PDF representing task."""
        cfg = req.config
        set_matplotlib_fontsize(cfg.PLOT_FONTSIZE)
        if CSS_PAGED_MEDIA:
            req.switch_output_to_png()
            # ... even weasyprint's SVG handling is inadequate
            html = self.get_pdf_html(req)
            return pdf_from_html(req, html)
        else:
            req.switch_output_to_svg()  # wkhtmltopdf can cope
            orientation = (
                "Landscape" if self.use_landscape_for_pdf else "Portrait"
            )
            return pdf_from_html(
                req,
                html=self.get_pdf_html(req),
                header_html=self.get_pdf_header_content(req),
                footer_html=self.get_pdf_footer_content(),
                extra_wkhtmltopdf_options={"orientation": orientation})

    def suggested_pdf_filename(self) -> str:
        """Suggested filename for PDF."""
        return get_export_filename(
            pls.PATIENT_SPEC_IF_ANONYMOUS,
            pls.PATIENT_SPEC,
            pls.TASK_FILENAME_SPEC,
            VALUE.OUTPUTTYPE_PDF,
            is_anonymous=self.is_anonymous,
            surname=self.patient.get_surname() if self.patient else "",
            forename=self.patient.get_forename() if self.patient else "",
            dob=self.patient.get_dob() if self.patient else None,
            sex=self.patient.get_sex() if self.patient else None,
            idnum_objects=self.patient.get_idnum_objects() if self.patient else None,  # noqa
            creation_datetime=self.get_creation_datetime(),
            basetable=self.tablename,
            serverpk=self._pk)

    def write_pdf_to_disk(self, req: CamcopsRequest, filename: str) -> None:
        """Writes PDF to disk, using filename."""
        pdffile = open(filename, "wb")
        pdffile.write(self.get_pdf(req))

    def get_pdf_html(self, req: CamcopsRequest) -> str:
        """Gets HTML used to make PDF (slightly different from plain HTML)."""
        signature = self.has_clinician
        return (
            self.get_pdf_start(req) +
            self.get_core_html(req) +
            self.get_office_html() +
            (SIGNATURE_BLOCK if signature else "") +
            PDFEND
        )

    def get_hyperlink_pdf(self, req: CamcopsRequest, text: str) -> str:
        """Hyperlink to PDF version."""
        return """<a href="{}" target="_blank">{}</a>""".format(
            get_url_task_pdf(req, self.tablename, self._pk),
            text
        )

    # -------------------------------------------------------------------------
    # Metadata for e.g. RiO
    # -------------------------------------------------------------------------

    def get_rio_metadata(self,
                         which_idnum: int,
                         uploading_user_id: str,
                         document_type: str) -> str:
        """Called by cc_hl7.send_to_filestore().

        From Servelec (Lee Meredith) to Rudolf Cardinal, 2014-12-04:

        Batch Document Upload

        The RiO batch document upload function can be used to upload documents
        in bulk automatically.  RiO includes a Batch Upload windows service
        which monitors a designated folder for new files.  Each file which is
        scanned must be placed in the designated folder along with a meta-data
        file which describes the document.  So essentially if a document had
        been scanned in and was called
        ‘ThisIsANewReferralLetterForAPatient.pdf’ then there would also need to
        be a meta file in the same folder called
        ‘ThisIsANewReferralLetterForAPatient.metadata’.  The contents of the
        meta file would need to include the following:

            Field Order; Field Name; Description; Data Mandatory (Y/N); Format

            1; ClientID; RiO Client ID which identifies the patient in RiO
            against which the document will be uploaded.; Y; 15 Alphanumeric
            Characters

            2; UserID; User ID of the uploaded document, this is any user
            defined within the RiO system and can be a single system user
            called ‘AutomaticDocumentUploadUser’ for example.; Y; 10
            Alphanumeric Characters

                [NB example longer than that!]

            3; DocumentType; The RiO defined document type eg: APT; Y; 80
            Alphanumeric Characters

            4; Title; The title of the document; N; 40 Alphanumeric Characters

            5; Description; The document description.; N; 500 Alphanumeric
            Characters

            6; Author; The author of the document; N; 80 Alphanumeric
            Characters

            7; DocumentDate; The date of the document; N; dd/MM/yyyy HH:mm

            8; FinalRevision; The revision values are 0 Draft or 1 Final,  this
            is defaulted to 1 which is Final revision.; N; 0 or 1

        As an example, this is what would be needed in a meta file:

            “1000001”,”TRUST1”,”APT”,”A title”, “A description of the
                document”, “An author”,”01/12/2012 09:45”,”1”

        (on one line)

        Clarification, from Lee Meredith to Rudolf Cardinal, 2015-02-18:

            - metadata files must be plain ASCII, not UTF-8
                ... here and cc_hl7.send_to_filestore()
            - line terminator is <CR>
                ... cc_hl7.send_to_filestore()
            - user name limit is 10 characters, despite incorrect example
                ... RecipientDefinition.check_valid()
            - DocumentType is a code that maps to a human-readable document
              type; for example, "APT" might map to "Appointment Letter". These
              mappings are specific to the local system. (We will probably want
              one that maps to "Clinical Correspondence" in the absence of
              anything more specific.)
            - RiO will delete the files after it's processed them.
            - Filenames should avoid spaces, but otherwise any other standard
              ASCII code is fine within filenames.
                ... cc_hl7.send_to_filestore()
        """

        try:
            client_id = self.patient.get_idnum_value(which_idnum)
        except AttributeError:
            client_id = ""
        title = "CamCOPS_" + self.shortname
        description = self.longname
        author = self.get_clinician_name()  # may be blank
        document_date = format_datetime_string(self.when_created,
                                               DATEFORMAT.RIO_EXPORT_UK)
        # This STRIPS the timezone information; i.e. it is in the local
        # timezone but doesn't tell you which timezone that is. (That's fine;
        # it should be local or users would be confused.)
        final_revision = (0 if self.is_live_on_tablet() else 1)

        item_list = [
            client_id,
            uploading_user_id,
            document_type,
            title,
            description,
            author,
            document_date,
            final_revision
        ]
        # UTF-8 is NOT supported by RiO for metadata. So:
        csv_line = ",".join([
            '"{}"'.format(mangle_unicode_to_ascii(x))
            for x in item_list
        ])
        return csv_line + "\n"

    # -------------------------------------------------------------------------
    # HTML components
    # -------------------------------------------------------------------------

    def get_html_start(self, req: CamcopsRequest) -> str:
        """Opening HTML, including CSS."""
        return (
            pls.WEBSTART +
            self.get_task_header_html(req)
        )

    def get_pdf_header_content(self, req: CamcopsRequest) -> str:
        anonymous = self.is_anonymous
        if anonymous:
            content = self.get_anonymous_page_header_html(req)
        else:
            content = self.patient.get_html_for_page_header(req)
        return pdf_header_content(content)

    def get_pdf_footer_content(self) -> str:
        taskname = ws.webify(self.shortname)
        created = format_datetime_string(self.when_created,
                                         DATEFORMAT.LONG_DATETIME)
        content = "{} created {}.".format(taskname, created)
        return pdf_footer_content(content)

    def get_pdf_start(self, req: CamcopsRequest) -> str:
        """Opening HTML for PDF, including CSS."""
        if CSS_PAGED_MEDIA:
            if self.use_landscape_for_pdf:
                head = PDF_HEAD_LANDSCAPE
            else:
                head = PDF_HEAD_PORTRAIT
            pdf_header_footer = (
                self.get_pdf_header_content(req) +
                self.get_pdf_footer_content()
            )
        else:
            head = PDF_HEAD_NO_PAGED_MEDIA
            pdf_header_footer = ""
        return (
            head +
            pdf_header_footer +
            pls.PDF_LOGO_LINE +
            self.get_task_header_html(req)
        )

    # noinspection PyMethodMayBeStatic
    def get_anonymous_page_header_html(self, req: CamcopsRequest) -> str:
        """Page header for anonymous tasks. Goes in the page margins for PDFs.
        """
        return req.wappstring("anonymous_task")


    def get_tablet_version(self) -> Version:
        return make_version(self._camcops_version)

    def get_superuser_nav_options(self,
                                  req: CamcopsRequest,
                                  offer_add_note: bool,
                                  offer_erase: bool,
                                  offer_edit_patient: bool) -> str:
        options = []
        if offer_add_note:
            options.append(
                '<a href="{}">Apply special note</a>'.format(
                    get_url_add_special_note(req,
                                             self.tablename, self._pk),
                )
            )
        if offer_erase and not self.is_erased() and self._era != ERA_NOW:
            # Note: prohibit manual erasure for non-finalized tasks.
            options.append(
                '<a href="{}">Erase task instance</a>'.format(
                    get_url_erase_task(req,
                                       self.tablename, self._pk),
                )
            )
        if (offer_edit_patient and
                not self.is_anonymous and
                self.patient and
                self._era != ERA_NOW):
            options.append(
                '<a href="{}">Edit patient details</a>'.format(
                    self.patient.get_url_edit_patient(req)
                )
            )
        if not options:
            return ""
        return """
            <div class="superuser">
                {}
            </div>
        """.format("<br>".join(options))

    # -------------------------------------------------------------------------
    # HTML elements used by tasks
    # -------------------------------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def get_standard_clinician_block(self) -> str:
        """
        HTML DIV for clinician information.
        Overridden by TaskHasClinicianMixin.
        """
        return ""

    # noinspection PyMethodMayBeStatic
    def get_standard_clinician_comments_block(self, comments: str) -> str:
        """HTML DIV for clinician's comments."""
        return """
            <div class="clinician">
                <table class="taskdetail">
                    <tr>
                        <td width="20%">Clinician’s comments:</td>
                        <td width="80%">{}</td>
                    </tr>
                </table>
            </div>
        """.format(
            ws.bold_if_not_blank(ws.webify(comments))
        )

    # noinspection PyMethodMayBeStatic
    def get_standard_respondent_block(self) -> str:
        """
        HTML DIV for respondent information.
        Overridden by TaskHasRespondentMixin
        """
        return ""

    def get_is_complete_td_pair(self, req: CamcopsRequest) -> str:
        """HTML to indicate whether task is complete or not, and to make it
        very obvious visually when it isn't."""
        c = self.is_complete()
        return """<td>Completed?</td>{}<b>{}</b></td>""".format(
            "<td>" if c else """<td class="incomplete">""",
            get_yes_no(req, c)
        )

    def get_is_complete_tr(self) -> str:
        """HTML table row to indicate whether task is complete or not, and to
        make it very obvious visually when it isn't."""
        return "<tr>" + self.get_is_complete_td_pair() + "</tr>"

    def get_twocol_val_row(self,
                           fieldname: str,
                           default: str = None,
                           label: str = None) -> str:
        """HTML table row, two columns, without web-safing of value."""
        val = getattr(self, fieldname)
        if val is None:
            val = default
        if label is None:
            label = fieldname
        return tr_qa(label, val)

    def get_twocol_string_row(self,
                              fieldname: str,
                              label: str = None) -> str:
        """HTML table row, two columns, with web-safing of value."""
        if label is None:
            label = fieldname
        return tr_qa(label, getattr(self, fieldname))

    def get_twocol_bool_row(self,
                            fieldname: str,
                            label: str = None) -> str:
        """HTML table row, two columns, with Boolean Y/N formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_yes_no_none(getattr(self, fieldname)))

    def get_twocol_bool_row_true_false(self,
                                       fieldname: str,
                                       label: str = None) -> str:
        """HTML table row, two columns, with Boolean T/F formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_true_false_none(getattr(self, fieldname)))

    def get_twocol_bool_row_present_absent(self,
                                           fieldname: str,
                                           label: str = None) -> str:
        """HTML table row, two columns, with Boolean P/A formatter."""
        if label is None:
            label = fieldname
        return tr_qa(label, get_present_absent_none(getattr(self, fieldname)))

    @staticmethod
    def get_twocol_picture_row(blob: Optional[Blob], label: str) -> str:
        """HTML table row, two columns, with PNG on right."""
        return tr(label, get_blob_img_html(blob))

    # -------------------------------------------------------------------------
    # Field helper functions for subclasses
    # -------------------------------------------------------------------------

    def get_values(self, fields: List[str]) -> List:
        """Get list of object's values from list of field names."""
        return [getattr(self, f) for f in fields]

    def is_field_complete(self, field: str) -> bool:
        """Is the field not None?"""
        return getattr(self, field) is not None

    def are_all_fields_complete(self, fields: List[str]) -> bool:
        """Are all fields not None?"""
        for f in fields:
            if getattr(self, f) is None:
                return False
        return True

    def n_complete(self, fields: List[str]) -> int:
        """How many of the fields are not None?"""
        total = 0
        for f in fields:
            if getattr(self, f) is not None:
                total += 1
        return total

    def n_incomplete(self, fields: List[str]) -> int:
        """How many of the fields are None?"""
        total = 0
        for f in fields:
            if getattr(self, f) is None:
                total += 1
        return total

    def count_booleans(self, fields: List[str]) -> int:
        """How many fields evaluate to True?"""
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value:
                total += 1
        return total

    def all_true(self, fields: List[str]) -> bool:
        """Do all fields evaluate to True?"""
        for f in fields:
            value = getattr(self, f)
            if not value:
                return False
        return True

    def count_where(self,
                    fields: List[str],
                    wherevalues: List[Any]) -> int:
        """Count how many field values are in wherevalues."""
        return sum(1 for x in self.get_values(fields) if x in wherevalues)

    def count_wherenot(self,
                       fields: List[str],
                       notvalues: List[Any]) -> int:
        """Count how many field values are NOT in notvalues."""
        return sum(1 for x in self.get_values(fields) if x not in notvalues)

    def sum_fields(self,
                   fields: List[str],
                   ignorevalue: Any = None) -> Union[int, float]:
        """Sum values stored in all fields (skipping any whose value is
        ignorevalue; treating fields containing None as zero)."""
        total = 0
        for f in fields:
            value = getattr(self, f)
            if value == ignorevalue:
                continue
            total += value if value is not None else 0
        return total

    def mean_fields(self,
                    fields: List[str],
                    ignorevalue: Any = None) -> Union[int, float, None]:
        """
        Mean of values stored in all fields (skipping any whose value is
        ignorevalue).
        """
        values = []
        for f in fields:
            value = getattr(self, f)
            if value != ignorevalue:
                values.append(value)
        try:
            return statistics.mean(values)
        except (TypeError, statistics.StatisticsError):
            return None

    @staticmethod
    def fieldnames_from_prefix(prefix: str, start: int, end: int) -> List[str]:
        return [prefix + str(x) for x in range(start, end + 1)]

    @staticmethod
    def fieldnames_from_list(prefix: str,
                             suffixes: Iterable[Any]) -> List[str]:
        return [prefix + str(x) for x in suffixes]

    # -------------------------------------------------------------------------
    # Extra strings
    # -------------------------------------------------------------------------

    def get_extrastring_taskname(self) -> str:
        return self.extrastring_taskname or self.tablename

    def extrastrings_exist(self) -> bool:
        return task_extrastrings_exist(self.get_extrastring_taskname())

    def wxstring(self,
                 req: CamcopsRequest,
                 name: str,
                 defaultvalue: str = None,
                 provide_default_if_none: bool = True) -> str:
        if defaultvalue is None and provide_default_if_none:
            defaultvalue = "[{}: {}]".format(self.get_extrastring_taskname(),
                                             name)
        return req.wxstring(
            self.get_extrastring_taskname(),
            name,
            defaultvalue,
            provide_default_if_none=provide_default_if_none)


# =============================================================================
# Fieldnames to auto-exempt from text filtering
# =============================================================================

@cache_region_static.cache_on_arguments(function_key_generator=fkg)
def text_filter_exempt_fields(task: Type[Task]) -> List[str]:
    exempt = []  # type: List[str]
    for attrname, column in gen_columns(task):
        if attrname.startswith("_") or not is_sqlatype_string(column.type):
            exempt.append(attrname)
    return exempt


# =============================================================================
# Ancillary
# =============================================================================

class Ancillary(object):
    """
    Abstract base class for subtables of tasks.

    Overridable attributes are a subset of those for Task.
    """
    # -------------------------------------------------------------------------
    # Attributes that must be provided
    # -------------------------------------------------------------------------
    tablename = None
    fkname = None
    fieldspecs = []

    # -------------------------------------------------------------------------
    # Attributes that can be overridden
    # -------------------------------------------------------------------------
    sortfield = None
    blob_name_idfield_list = []

    @classmethod
    def get_full_fieldspecs(cls) -> FIELDSPECLIST_TYPE:
        full_fieldspecs = list(STANDARD_ANCILLARY_FIELDSPECS)  # copy
        full_fieldspecs.extend(cls.fieldspecs)
        return full_fieldspecs

    @classmethod
    def get_fieldnames(cls) -> List[str]:
        return [x["name"] for x in cls.get_full_fieldspecs()]

    def __init__(self, serverpk: int = None) -> None:
        """Only call with serverpk=None if you will populate all fields
        manually (see e.g.
        get_contemporaneous_matching_ancillary_objects_by_fk)."""
        if serverpk is not None:
            pls.db.fetch_object_from_db_by_pk(
                self,
                self.tablename,
                self.get_fieldnames(),
                serverpk)

    # *** move to GenericTabletRecordMixin
    def make_xml_branches_for_blob_fields(
            self, skip_fields: List[str] = None) -> List[XmlElement]:
        """Returns list of XmlElementTuple elements for BLOB fields."""
        skip_fields = skip_fields or []
        return make_xml_branches_for_blob_fields(self, skip_fields=skip_fields)

    # *** move to GenericTabletRecordMixin
    def get_blob_xml_tuple(self,
                           blobid: int,
                           name: str) -> XmlElement:
        """Get XmlElementTuple for a PNG BLOB."""
        return get_blob_xml_tuple(self, blobid, name)

    # *** move to GenericTabletRecordMixin
    def get_blob_by_id(self, blobid: int) -> Optional[Blob]:
        """Get Blob() object from blob ID, or None."""
        return get_blob_by_id(self, blobid)

    # *** move to GenericTabletRecordMixin
    def get_cris_fieldspecs_values(self, common_fsv: FIELDSPECLIST_TYPE) \
            -> FIELDSPECLIST_TYPE:
        fieldspecs = copy.deepcopy(self.get_full_fieldspecs())
        for fs in fieldspecs:
            fs["value"] = getattr(self, fs["name"])
        return common_fsv + fieldspecs


# =============================================================================
# BLOB functions (shared between Task and Ancillary)
# =============================================================================

def make_xml_branches_for_blob_fields(
        obj: Union[Task, Ancillary], 
        skip_fields: bool = None) -> List[XmlElement]:
    """Returns list of XmlElementTuple elements for BLOB fields."""
    skip_fields = skip_fields or []
    branches = []
    for t in obj.blob_name_idfield_list:
        name = t[0]
        blobid_field = t[1]
        if blobid_field in skip_fields:
            continue
        blobid = getattr(obj, blobid_field)
        branches.append(
            obj.get_blob_xml_tuple(blobid, name)
        )
    return branches


def get_blob_xml_tuple(obj: Union[Task, Ancillary],
                       blobid: int,
                       name: str) -> XmlElement:
    """Get XmlElementTuple for a PNG BLOB."""
    blob = obj.get_blob_by_id(blobid)
    if blob is None:
        return get_xml_blob_tuple(name, None)
    return blob.get_image_xml_tuple(name)


def get_blob_by_id(obj: Union[Task, Ancillary],
                   blobid: int) -> Optional[Blob]:
    """Get Blob() object from blob ID, or None."""
    if blobid is None:
        return None
    # noinspection PyProtectedMember
    return get_contemporaneous_blob_by_client_info(
        obj._device_id, blobid, obj._era,
        obj._when_added_batch_utc, obj._when_removed_batch_utc)


# =============================================================================
# Cross-class generators and the like
# =============================================================================

def gen_tasks_matching_session_filter(
        session: 'CamcopsSession') -> Generator[Task, None, None]:
    """Generate tasks that match the session's filter settings."""

    # Find candidate tasks meeting the filters
    cls_pk_wc = []
    for cls in Task.all_subclasses():
        if cls.filter_allows_task_type(session):
            pk_wc = cls.get_session_candidate_task_pks_whencreated(session)
            for row in pk_wc:
                if row[1] is None:
                    log.warning("Blank when_created: cls={}, _pk={}, "
                                "when_created={}", cls, row[0], row[1])
                    # ... will crash at the sort stage
                cls_pk_wc.append((cls, row[0], row[1]))
    # Sort by when_created (conjointly across task classes)
    cls_pk_wc = sorted(cls_pk_wc, key=second_item_or_min, reverse=True)
    # Yield those that really do match the filter
    for cls, pk, wc in cls_pk_wc:
        task = cls(pk)
        if task is not None and task.is_compatible_with_filter(session):
            yield task
    # *** CHANGE THIS: inefficient; runs multiple queries where one would do


def gen_tasks_live_on_tablet(device_id: int) -> Generator[Task, None, None]:
    """Generate tasks that are live on the device.
    Includes non-current ones."""

    cls_pk_wc = []
    for cls in Task.all_subclasses():
        table = cls.tablename
        wcfield_utc = cls.whencreated_fieldexpr_as_utc()
        query = """
            SELECT  _pk, {wcfield_utc}
            FROM    {t}
            WHERE   _era = ?
            AND     _device_id = ?
        """.format(
            wcfield_utc=wcfield_utc,
            t=table,
        )
        args = [ERA_NOW, device_id]
        pk_wc = pls.db.fetchall(query, *args)
        cls_pk_wc.extend([(cls, row[0], row[1]) for row in pk_wc])
    # Sort by when_created (conjointly across task classes)
    cls_pk_wc = sorted(cls_pk_wc, key=second_item_or_min, reverse=True)
    # Yield them up
    for cls, pk, wc in cls_pk_wc:
        task = cls(pk)
        if task is not None:
            yield task
    # *** CHANGE THIS: inefficient; runs multiple queries where one would do


def gen_tasks_using_patient(patient_id: int,
                            device_id: int,
                            era: str) -> Generator[Task, None, None]:
    """Generate tasks sharing a particular patient record.
    Includes non-current ones."""

    cls_pk_wc = []
    for cls in Task.all_subclasses():
        if cls.is_anonymous:
            continue
        table = cls.tablename
        wcfield_utc = cls.whencreated_fieldexpr_as_utc()
        query = """
            SELECT  _pk, {wcfield_utc}
            FROM    {t}
            WHERE   patient_id = ?
            AND     _device_id = ?
            AND     _era = ?
        """.format(
            wcfield_utc=wcfield_utc,
            t=table,
        )
        args = [
            patient_id,
            device_id,
            era
        ]
        pk_wc = pls.db.fetchall(query, *args)
        cls_pk_wc.extend([(cls, row[0], row[1]) for row in pk_wc])
    # Sort by when_created (conjointly across task classes)
    cls_pk_wc = sorted(cls_pk_wc, key=second_item_or_min, reverse=True)
    # Yield them up
    for cls, pk, wc in cls_pk_wc:
        task = cls(pk)
        if task is not None:
            yield task
    # *** CHANGE THIS: inefficient; runs multiple queries where one would do


def gen_tasks_for_patient_deletion(
        which_idnum: int, idnum_value: int) -> Generator[Task, None, None]:
    """Generate tasks to be affected by a delete-patient command."""

    cls_pk_wc = []
    for cls in Task.all_subclasses():
        if cls.is_anonymous:
            continue
        pk_wc = cls.get_task_pks_wc_for_patient_deletion(which_idnum,
                                                         idnum_value)
        cls_pk_wc.extend([(cls, row[0], row[1]) for row in pk_wc])
    # Sort by when_created (conjointly across task classes)
    cls_pk_wc = sorted(cls_pk_wc, key=second_item_or_min, reverse=True)
    # Yield them up
    for cls, pk, wc in cls_pk_wc:
        task = cls(pk)
        if task is not None:
            yield task
    # *** CHANGE THIS: inefficient; runs multiple queries where one would do


# =============================================================================
# Tables used by tasks suitable for HL-7 export (i.e. not anonymous ones)
# =============================================================================

def get_base_tables(include_anonymous: bool = True) -> List[str]:
    """Get a list of all tasks' base tables."""
    return [
        cls.tablename
        for cls in Task.all_subclasses_by_tablename()
        if (not cls.is_anonymous or include_anonymous)
    ]


# =============================================================================
# Support functions
# =============================================================================

def get_task_filter_dropdown(currently_selected: str = None) -> str:
    """Iterates through all tasks, generating a drop-down list."""
    taskoptions = []
    for cls in Task.all_subclasses_by_shortname():
        t = ws.webify(cls.tablename)
        taskoptions.append({
            "shortname": cls.shortname,
            "html": """<option value="{t}"{sel}>{name}</option>""".format(
                t=t,
                name=ws.webify(cls.shortname),
                sel=ws.option_selected(currently_selected, t),
            )
        })
    return """
        <select name="{}">
            <option value="">(all)</option>
    """.format(PARAM.TASK) + "".join(
        [taskopt["html"] for taskopt in taskoptions]
    ) + "</select>"


def get_from_dict(d: Dict, key: str, default: Any = INVALID_VALUE) -> Any:
    """Returns a value from a dictionary."""
    return d.get(key, default)


# =============================================================================
# Reports
# =============================================================================

class TaskCountReport(Report):
    """Report to count task instances."""
    report_id = "taskcount"
    report_title = "(Server) Count current task instances, by creation date"
    param_spec_list = []

    def get_rows_descriptions(self, req: CamcopsRequest,
                              **kwargs: Any) -> REPORT_RESULT_TYPE:
        final_rows = []
        fieldnames = []
        dbsession = req.dbsession
        classes = Task.all_subclasses_by_tablename()
        for cls in classes:
            sql = """
                SELECT
                    '{tablename}' AS task,
                    YEAR(_when_added_batch_utc) AS year,
                    MONTH(_when_added_batch_utc) AS month,
                    COUNT(*) AS num_tasks_added
                FROM {tablename}
                WHERE _current
                GROUP BY
                    YEAR(_when_added_batch_utc),
                    MONTH(_when_added_batch_utc)
                ORDER BY
                    YEAR(_when_added_batch_utc),
                    MONTH(_when_added_batch_utc) DESC
            """.format(
                tablename=cls.tablename,
            )
            rows, fieldnames = get_rows_fieldnames_from_raw_sql(dbsession, sql)
            final_rows.extend(rows)
        return final_rows, fieldnames


# =============================================================================
# URLs
# =============================================================================

def get_url_task(req: CamcopsRequest,
                 tablename: str, serverpk: int, outputtype: str) -> str:
    """URL to view a particular task."""
    url = get_generic_action_url(req, ACTION.TASK)
    url += get_url_field_value_pair(PARAM.OUTPUTTYPE, outputtype)
    url += get_url_field_value_pair(PARAM.TABLENAME, tablename)
    url += get_url_field_value_pair(PARAM.SERVERPK, serverpk)
    return url


def get_url_task_pdf(req: CamcopsRequest,
                     tablename: str, serverpk: int) -> str:
    """URL to view a particular task as PDF."""
    return get_url_task(req, tablename, serverpk, VALUE.OUTPUTTYPE_PDF)


def get_url_task_html(req: CamcopsRequest,
                      tablename: str, serverpk: int) -> str:
    """URL to view a particular task as HTML."""
    return get_url_task(req, tablename, serverpk, VALUE.OUTPUTTYPE_HTML)


def get_url_task_xml(req: CamcopsRequest,
                     tablename: str, serverpk: int) -> str:
    """URL to view a particular task as XML (with default options)."""
    url = get_url_task(req, tablename, serverpk, VALUE.OUTPUTTYPE_XML)
    url += get_url_field_value_pair(PARAM.INCLUDE_BLOBS, 1)
    url += get_url_field_value_pair(PARAM.INCLUDE_CALCULATED, 1)
    url += get_url_field_value_pair(PARAM.INCLUDE_PATIENT, 1)
    url += get_url_field_value_pair(PARAM.INCLUDE_COMMENTS, 1)
    return url


def get_url_erase_task(req: CamcopsRequest,
                       tablename: str, serverpk: int) -> str:
    url = get_generic_action_url(req, ACTION.ERASE_TASK)
    url += get_url_field_value_pair(PARAM.TABLENAME, tablename)
    url += get_url_field_value_pair(PARAM.SERVERPK, serverpk)
    return url


def get_url_add_special_note(req: CamcopsRequest,
                             tablename: str, serverpk: int) -> str:
    url = get_generic_action_url(req, ACTION.ADD_SPECIAL_NOTE)
    url += get_url_field_value_pair(PARAM.TABLENAME, tablename)
    url += get_url_field_value_pair(PARAM.SERVERPK, serverpk)
    return url


# =============================================================================
# Unit testing
# =============================================================================

def require_implementation(class_name: str,
                           instance: Task,
                           method_name: str) -> None:
    if not derived_class_implements_method(instance, Task, method_name):
        raise NotImplementedError("class {} must implement {}".format(
            class_name, method_name
        ))


def task_class_unit_test(cls: Type[Task]) -> None:
    unit_test_require_truthy_attribute(cls, 'tablename')
    unit_test_require_truthy_attribute(cls, 'shortname')
    unit_test_require_truthy_attribute(cls, 'longname')
    if cls.fieldspecs is None:
        raise AssertionError("Class {} has fieldspecs = None".format(
            get_object_name(cls)))
    fieldnames = cls.get_fieldnames()
    # No duplicate field names
    # noinspection PyArgumentList
    duplicate_fieldnames = [
        x for x, count in collections.Counter(fieldnames).items() if count > 1]
    if duplicate_fieldnames:
        raise AssertionError("Class {}: duplicate fieldnames: {}".format(
            get_object_name(cls), duplicate_fieldnames))
    # Field names don't conflict with object attributes
    attributes = list(cls.__dict__)
    conflict = set(attributes).intersection(set(fieldnames))
    if conflict:
        raise AssertionError(
            "Fields conflict with object attributes in class {}: {}".format(
                cls.__name__, conflict))


def ancillary_class_unit_test(cls: Type[Ancillary]) -> None:
    unit_test_require_truthy_attribute(cls, 'tablename')
    unit_test_require_truthy_attribute(cls, 'fkname')
    unit_test_require_truthy_attribute(cls, 'fieldspecs')
    # Field names don't conflict
    attributes = list(cls.__dict__)
    fieldnames = cls.get_fieldnames()
    conflict = set(attributes).intersection(set(fieldnames))
    if conflict:
        raise AssertionError(
            "Fields conflict with object attributes: {}".format(conflict))


def task_instance_unit_test(req: CamcopsRequest,
                            name: str,
                            instance: Task) -> None:
    """Unit test for an named instance of Task."""

    # *** req: CamcopsRequest

    recipient_def = RecipientDefinition(
        valid_which_idnums=pls.get_which_idnums())

    # -------------------------------------------------------------------------
    # Test methods
    # -------------------------------------------------------------------------
    # Core things to override
    unit_test_ignore("Testing {}.is_complete".format(name),
                     instance.is_complete)
    unit_test_ignore("Testing {}.get_task_html".format(name),
                     instance.get_task_html)

    # not make_tables
    unit_test_ignore("Testing {}.get_fieldnames".format(name),
                     instance.get_fieldnames)
    unit_test_ignore("Testing {}.get_extra_table_names".format(name),
                     instance.get_extra_table_names)

    if instance.provides_trackers:
        unit_test_ignore("Testing {}.get_trackers".format(name),
                         instance.get_trackers)

    unit_test_ignore("Testing {}.get_clinical_text".format(name),
                     instance.get_clinical_text)

    unit_test_ignore("Testing {}.get_summaries".format(name),
                     instance.get_summaries)
    # not make_extra_summary_tables
    unit_test_ignore("Testing {}.get_extra_summary_table_names".format(name),
                     instance.get_extra_summary_table_names)

    unit_test_ignore("Testing {}.get_extra_dictlist_for_tsv".format(
        name), instance.get_extra_dictlist_for_tsv)

    literals = ["hello"]
    datetimes = [datetime.date(2014, 1, 1)]
    regexes = (
        [get_literal_regex(x) for x in literals] +
        [get_date_regex(dt) for dt in datetimes]
    )

    unit_test_ignore("Testing {}.get_fields".format(name),
                     instance.get_fields)
    unit_test_ignore("Testing {}.field_contents_valid".format(name),
                     instance.field_contents_valid)
    unit_test_ignore("Testing {}.field_contents_invalid_because".format(name),
                     instance.field_contents_invalid_because)
    unit_test_ignore("Testing {}.get_blob_fields".format(name),
                     instance.get_blob_fields)

    unit_test_ignore("Testing {}.is_preserved".format(name),
                     instance.is_preserved)

    unit_test_ignore("Testing {}.get_creation_datetime".format(name),
                     instance.get_creation_datetime)
    unit_test_ignore("Testing {}.get_creation_datetime_utc".format(name),
                     instance.get_creation_datetime_utc)
    unit_test_ignore("Testing {}.get_seconds_from_creation_to_"
                     "first_finish".format(name),
                     instance.get_seconds_from_creation_to_first_finish)
    unit_test_ignore("Testing {}.whencreated_field_iso8601".format(name),
                     instance.whencreated_field_iso8601)
    unit_test_ignore("Testing {}.whencreated_fieldexpr_as_utc".format(name),
                     instance.whencreated_fieldexpr_as_utc)
    unit_test_ignore("Testing {}.whencreated_fieldexpr_as_local".format(name),
                     instance.whencreated_fieldexpr_as_local)

    unit_test_ignore("Testing {}.get_standard_summary_table_name".format(name),
                     instance.get_standard_summary_table_name)
    unit_test_ignore("Testing {}.provides_summaries".format(name),
                     instance.provides_summaries)
    # not make_summary_table
    # not make_standard_summary_table
    unit_test_ignore("Testing {}.is_complete_summary_field".format(name),
                     instance.is_complete_summary_field)
    unit_test_ignore("Testing {}.get_summary_names".format(name),
                     instance.get_summary_names)

    unit_test_ignore("Testing {}.get_all_table_and_view_names".format(name),
                     instance.get_all_table_and_view_names)

    # not get_blob

    unit_test_ignore("Testing {}.dump".format(name), instance.dump)

    # not tested: apply_special_note

    unit_test_ignore("Testing {}.get_clinician_name".format(name),
                     instance.get_clinician_name)

    unit_test_ignore("Testing {}.is_female".format(name),
                     instance.is_female)
    unit_test_ignore("Testing {}.is_male".format(name),
                     instance.is_male)
    unit_test_ignore("Testing {}.get_patient_server_pk".format(name),
                     instance.get_patient_server_pk)
    unit_test_ignore("Testing {}.get_patient".format(name),
                     instance.get_patient)
    unit_test_ignore("Testing {}.get_patient_forename".format(name),
                     instance.get_patient_forename)
    unit_test_ignore("Testing {}.get_patient_surname".format(name),
                     instance.get_patient_surname)
    unit_test_ignore("Testing {}.get_patient_dob".format(name),
                     instance.get_patient_dob)
    unit_test_ignore("Testing {}.get_patient_sex".format(name),
                     instance.get_patient_sex)
    unit_test_ignore("Testing {}.get_patient_address".format(name),
                     instance.get_patient_address)
    unit_test_ignore("Testing {}.get_patient_idnum_objects".format(name),
                     instance.get_patient_idnum_objects)
    unit_test_ignore("Testing {}.get_patient_idnum_object(1)".format(name),
                     instance.get_patient_idnum_object, 1)
    unit_test_ignore("Testing {}.get_patient_hl7_pid_segment".format(name),
                     instance.get_patient_hl7_pid_segment, recipient_def)

    unit_test_ignore("Testing {}.get_hl7_data_segments".format(name),
                     instance.get_hl7_data_segments, recipient_def)
    unit_test_ignore("Testing {}.get_hl7_extra_data_segments".format(name),
                     instance.get_hl7_extra_data_segments, recipient_def)
    # not tested: delete_from_hl7_message_log

    # not tested: audit
    # not tested: save
    # not tested: manually_erase
    unit_test_ignore("Testing {}.get_server_pks_of_record_group".format(name),
                     instance.get_server_pks_of_record_group)
    unit_test_ignore("Testing {}.is_erased".format(name), instance.is_erased)
    # not tested: erase_subtable_records_even_noncurrent

    # not tested: get_task_pks_for_patient_deletion
    # not tested: delete_entirely
    # not tested: delete_subtable_records_even_noncurrent
    unit_test_ignore("Testing {}.get_blob_ids".format(name),
                     instance.get_blob_ids)
    unit_test_ignore("Testing {}.get_blob_pks_of_record_group".format(name),
                     instance.get_blob_pks_of_record_group)

    unit_test_ignore("Testing {}.get_task_list_row".format(name),
                     instance.get_task_list_row)

    # not tested: get_session_candidate_task_pks_whencreated
    # not tested: allowed_to_user
    # not tested: filter_allows_task_type
    # not tested: is_compatible_with_filter
    # not tested: compatible_with_text_filter

    # not tested: get_task_pks_for_tracker
    # not tested: get_task_pks_for_clinical_text_view
    # not tested: get_task_pks_for_tracker_or_clinical_text_view

    unit_test_ignore("Testing {}.get_all_current_pks".format(name),
                     instance.get_all_current_pks)
    # not tested: gen_all_current_tasks
    # not tested: gen_all_tasks_matching_session_filter

    unit_test_ignore("Testing {}.get_dictlist_for_tsv".format(
        name), instance.get_dictlist_for_tsv)
    dictlist = instance.get_dictlist_for_tsv(req)
    if len(dictlist) == 0:
        raise AssertionError("get_dictlist_for_tsv: zero-length result")
    for d in dictlist:
        if "filenamestem" not in d:
            raise AssertionError("get_dictlist_for_tsv: no filenamestem")
        if "rows" not in d:
            raise AssertionError("get_dictlist_for_tsv: no rows")
        rows = d.get("rows")
        if rows is None:
            raise AssertionError("get_dictlist_for_tsv: rows is None")
        if len(rows) == 0:
            continue
        r = rows[0]  # as a specimen row
        if r is None:
            raise AssertionError("get_dictlist_for_tsv: first row is None")

    unit_test_verify_not("Testing {}.get_xml".format(name),
                         instance.get_xml,
                         include_calculated=False, include_blobs=False,
                         include_patient=False, indent_spaces=4, eol='\n',
                         skip_fields=None, include_comments=False,
                         must_not_return=None)
    unit_test_verify_not("Testing {}.get_xml".format(name),
                         instance.get_xml,
                         include_calculated=True, include_blobs=True,
                         include_patient=True, indent_spaces=4, eol='\n',
                         skip_fields=None, include_comments=True,
                         must_not_return=None)
    unit_test_ignore("Testing {}.get_xml_root".format(name),
                     instance.get_xml_root)
    unit_test_ignore("Testing {}.get_xml_core_branches".format(name),
                     instance.get_xml_core_branches)
    unit_test_ignore("Testing {}.make_xml_branches_for_blob_fields".format(
        name), instance.make_xml_branches_for_blob_fields)
    # not tested: get_blob_xml_tuple

    unit_test_verify_not("Testing {}.get_html".format(name),
                         instance.get_html,
                         must_not_return=None)
    unit_test_ignore("Testing {}.get_hyperlink_html".format(name),
                     instance.get_hyperlink_html, "HTML")

    unit_test_ignore("Testing {}.suggested_pdf_filename".format(name),
                     instance.suggested_pdf_filename)
    # not write_pdf_to_disk
    unit_test_ignore("Testing {}.get_pdf_html".format(name),
                     instance.get_pdf_html)
    unit_test_ignore("Testing {}.get_hyperlink_pdf".format(name),
                     instance.get_hyperlink_pdf, "PDF")

    unit_test_ignore("Testing {}.get_html_start".format(name),
                     instance.get_html_start)
    unit_test_ignore("Testing {}.get_pdf_start".format(name),
                     instance.get_pdf_start)
    unit_test_ignore("Testing {}.get_anonymous_page_header_html".format(name),
                     instance.get_anonymous_page_header_html)
    unit_test_ignore("Testing {}.get_anonymous_task_header_html".format(name),
                     instance.get_anonymous_task_header_html)
    unit_test_ignore("Testing {}.get_task_header_html".format(name),
                     instance.get_task_header_html)
    unit_test_ignore("Testing {}.get_not_current_warning".format(name),
                     instance.get_not_current_warning)
    unit_test_ignore("Testing {}.get_invalid_warning".format(name),
                     instance.get_invalid_warning)
    unit_test_ignore("Testing {}.get_erasure_notice".format(name),
                     instance.get_erasure_notice)
    unit_test_ignore("Testing {}.get_special_notes".format(name),
                     instance.get_special_notes_html)
    unit_test_ignore("Testing {}.get_office_html".format(name),
                     instance.get_office_html)
    unit_test_ignore("Testing {}.get_xml_nav_html".format(name),
                     instance.get_xml_nav_html)
    unit_test_ignore("Testing {}.get_superuser_nav_options".format(name),
                     instance.get_superuser_nav_options, True, True, True)
    unit_test_ignore("Testing {}.get_predecessor_html_line".format(name),
                     instance.get_predecessor_html_line)
    unit_test_ignore("Testing {}.get_successor_html_line".format(name),
                     instance.get_successor_html_line)

    unit_test_ignore("Testing {}.get_standard_clinician_block".format(name),
                     instance.get_standard_clinician_block)
    unit_test_ignore("Testing {}.get_standard_clinician_comments_block".format(
        name), instance.get_standard_clinician_comments_block, "blahblah")
    # some helper functions here not tested

    # -------------------------------------------------------------------------
    # Test inheritance; are the necessary extras implemented?
    # -------------------------------------------------------------------------
    depclasslist = instance.dependent_classes
    for depclass in depclasslist:
        ancillary_class_unit_test(depclass)

    infolist = instance.extra_summary_table_info
    now = get_now_utc()
    data = instance.get_extra_summary_table_data(now)
    ntables = len(infolist)
    if len(data) != ntables:
        raise AssertionError(
            "extra_summary_table_info: different # tables [{}] to "
            "get_extra_summary_table_data() [{}]".format(ntables, len(data)))
    for i in range(ntables):
        for row_valuelist in data[i]:
            if len(row_valuelist) != len(infolist[i]["fieldspecs"]):
                raise AssertionError(
                    "extra_summary_table_info: different # fields [{}] to"
                    " get_extra_summary_table_data() "
                    "[{}]".format(len(infolist[i]), len(row_valuelist)))

    # -------------------------------------------------------------------------
    # Ensure the summary names don't overlap with the field names, etc.
    # -------------------------------------------------------------------------
    field_names = instance.get_fields()
    summary_names = instance.get_summary_names(req)
    if set(field_names).intersection(set(summary_names)):
        raise AssertionError("Summary field names overlap with main field "
                             "names")

    field_and_summary_names = field_names + summary_names
    for f in Patient.FIELDS:
        test_field = TSV_PATIENT_FIELD_PREFIX + f
        if test_field in field_and_summary_names:
            raise AssertionError(
                "Prefixed patient field {} (as {}) conflicts with a "
                "main field or summary field name".format(f, test_field)
            )

    # -------------------------------------------------------------------------
    # Ensure field types are valid
    # -------------------------------------------------------------------------
    fieldspeclist = instance.get_full_fieldspecs()
    for fs in fieldspeclist:
        cc_db.ensure_valid_cctype(fs["cctype"])
    summarylist = instance.get_summaries(req)
    for fs in summarylist:
        cc_db.ensure_valid_cctype(fs["cctype"])

    # -------------------------------------------------------------------------
    # Any task-specific unit tests?
    # -------------------------------------------------------------------------
    unit_test_ignore("Calling {}.unit_tests".format(name),
                     instance.unit_tests)


# noinspection PyUnusedLocal
def task_instance_unit_test_slow(name: str,
                                 instance: Task,
                                 skip_tasks: List[str] = None) -> None:
    unit_test_ignore("Testing {}.get_pdf".format(name),
                     instance.get_pdf)


def task_unit_test(req: CamcopsRequest, cls: Type[Task]) -> None:
    """Unit test for a Task subclass."""
    name = cls.__name__
    # Test class framework
    task_class_unit_test(cls)
    # Test creation with a numeric PK, which may or may not exist in the DB
    unit_test_ignore("Testing {}.__init__(0)".format(name),
                     cls, 0)
    # Test creation with a blank PK
    unit_test_ignore("Testing {}.__init__(None)".format(name),
                     cls, None)
    # Find (if one exists) an actual task that's current, and test with that
    # and a "fresh" task initialized with a blank PK
    current_pks = pls.db.fetchallfirstvalues(
        "SELECT _pk FROM {} WHERE _current".format(cls.tablename)
    )
    test_pks = [None, current_pks[0]] if current_pks else [None]
    for pk in test_pks:
        task_instance_unit_test(req, name, cls(pk))

    # Other classmethod tests


def cctask_unit_tests() -> None:
    """Unit tests for cc_task module."""
    unit_test_ignore("", task_factory, "xxx", 0)
    unit_test_ignore("", task_factory, "phq9", 0)
    unit_test_show("", get_base_tables, True)
    unit_test_show("", get_base_tables, False)
    unit_test_ignore("", get_literal_regex, "hello")
    unit_test_verify("", get_type_size_as_text_from_sqltype,
                     ("INT", ""), "INT")
    unit_test_verify("", get_type_size_as_text_from_sqltype,
                     ("VARCHAR", "10"), "VARCHAR(10)")

    unit_test_ignore("", get_task_filter_dropdown)
    unit_test_ignore("", get_url_task_pdf, "nonexistenttable", 3)
    unit_test_ignore("", get_url_task_html, "nonexistenttable", 3)
    unit_test_ignore("", get_url_task_xml, "nonexistenttable", 3)
    unit_test_ignore("", get_url_erase_task, "nonexistenttable", 3)
    unit_test_ignore("", get_url_add_special_note, "nonexistenttable", 3)
    pls.db.rollback()

    skip_tasks = []
    classes = Task.all_subclasses_by_shortname()
    longnames = set()
    shortnames = set()
    tasktables = set()
    for cls in classes:
        # Sanity checking
        ln = cls.longname
        if ln in longnames:
            raise AssertionError(
                "Task longname ({}) duplicates another".format(ln))
        longnames.add(ln)

        sn = cls.shortname
        if sn in shortnames:
            raise AssertionError(
                "Task shortname ({}) duplicates another".format(sn))
        shortnames.add(sn)

        basetable = cls.tablename
        if basetable in tasktables:
            raise AssertionError(
                "Task basetable ({}) duplicates another".format(basetable))
        tasktables.add(basetable)

        extratables = cls.get_extra_table_names()
        for t in extratables:
            if t in tasktables:
                raise AssertionError(
                    "Task extratable ({}) duplicates another".format(t))
            tasktables.add(t)

        if cls.tablename in skip_tasks:
            continue

        # Task unit tests
        task_unit_test(req, cls)
        pls.db.rollback()

    for cls in classes:
        if cls.tablename in skip_tasks:
            continue
        # Slow task unit tests
        instance = cls(None)
        task_instance_unit_test_slow(cls.__name__, instance)
        pls.db.rollback()


def cctask_unit_tests_basic() -> None:
    "Preliminary quick checks."""
    classes = Task.all_subclasses_by_tablename()
    for cls in classes:
        task_class_unit_test(cls)
