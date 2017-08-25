#!/usr/bin/env python
# camcops_server/tasks/demoquestionnaire.py

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
"""

from typing import Any, Dict, List, Tuple, Type

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Float, Integer, Time, UnicodeText

from ..cc_modules.cc_blob import blob_relationship
from ..cc_modules.cc_db import add_multiple_columns
from ..cc_modules.cc_html import answer
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqla_coltypes import (
    CamcopsColumn,
    DateTimeAsIsoTextColType,
    DiagnosticCodeColType,
)
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_task import Task


# =============================================================================
# TASKS: DEMO QUESTIONNAIRE
# =============================================================================

N_MCQ = 10  # 8 in v1; 10 in v2
N_MCQBOOL = 3
N_MULTIPLERESPONSE = 6
N_BOOLTEXT = 22
N_BOOLIMAGE = 2
N_PICKER = 2
N_SLIDER = 2


def divtest(divname: str) -> str:
    return '<div class="{d}">.{d}</div>\n'.format(d=divname)


class DemoQuestionnaireMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['DemoQuestionnaire'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(cls, "mcq", 1, N_MCQ)
        add_multiple_columns(cls, "mcqbool", 1, N_MCQBOOL)
        add_multiple_columns(cls, "multipleresponse", 1, N_MULTIPLERESPONSE)
        add_multiple_columns(cls, "booltext", 1, N_BOOLTEXT)
        add_multiple_columns(cls, "boolimage", 1, N_BOOLIMAGE)
        add_multiple_columns(cls, "picker", 1, N_PICKER)
        add_multiple_columns(cls, "slider", 1, N_SLIDER, Float)
        super().__init__(name, bases, classdict)


class DemoQuestionnaire(Task, Base,
                        metaclass=DemoQuestionnaireMetaclass):
    __tablename__ = "demoquestionnaire"
    shortname = "Demo"
    longname = "Demonstration Questionnaire"
    is_anonymous = True

    mcqtext_1a = Column("mcqtext_1a", UnicodeText)
    mcqtext_1b = Column("mcqtext_1b", UnicodeText)
    mcqtext_2a = Column("mcqtext_2a", UnicodeText)
    mcqtext_2b = Column("mcqtext_2b", UnicodeText)
    mcqtext_3a = Column("mcqtext_3a", UnicodeText)
    mcqtext_3b = Column("mcqtext_3b", UnicodeText)
    typedvar_text = Column("typedvar_text", UnicodeText)
    typedvar_text_multiline = Column("typedvar_text_multiline", UnicodeText)
    typedvar_text_rich = Column("typedvar_text_rich", UnicodeText)  # v2
    typedvar_int = Column("typedvar_int", Integer)
    typedvar_real = Column("typedvar_real", Float)
    date_only = Column("date_only", DateTimeAsIsoTextColType)
    date_time = Column("date_time", DateTimeAsIsoTextColType)
    thermometer = Column("thermometer", Integer)
    diagnosticcode_code = Column("diagnosticcode_code", DiagnosticCodeColType)
    diagnosticcode_description = Column(
        "diagnosticcode_description", UnicodeText
    )
    diagnosticcode2_code = Column(
        "diagnosticcode2_code", DiagnosticCodeColType
    )  # v2
    diagnosticcode2_description = Column(
        "diagnosticcode2_description", UnicodeText
    )  # v2
    photo_blobid = CamcopsColumn(
        "photo_blobid", Integer,
        is_blob_id_field=True, blob_relationship_attr_name="photo"
    )
    # IGNORED. REMOVE WHEN ALL PRE-2.0.0 TABLETS GONE:
    photo_rotation = Column("photo_rotation", Integer)  # *** DEFUNCT as of v2.0.0  # noqa
    canvas_blobid = CamcopsColumn(
        "canvas_blobid", Integer,
        is_blob_id_field=True, blob_relationship_attr_name="canvas"
    )
    canvas2_blobid = CamcopsColumn(
        "canvas2_blobid", Integer,
        is_blob_id_field=True, blob_relationship_attr_name="canvas2"
    )
    spinbox_int = Column("spinbox_int", Integer)  # v2
    spinbox_real = Column("spinbox_real", Float)  # v2
    time_only = Column("time_only", Time)  # v2

    photo = blob_relationship("DemoQuestionnaire", "photo_blobid")
    canvas = blob_relationship("DemoQuestionnaire", "canvas_blobid")
    canvas2 = blob_relationship("DemoQuestionnaire", "canvas2_blobid")

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                </table>
            </div>
            <div class="explanation">
                This is a demo questionnaire, containing no genuine
                information.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
        )
        for i in range(1, N_MCQ + 1):
            h += self.get_twocol_val_row("mcq" + str(i))
        for i in range(1, N_MCQBOOL + 1):
            h += self.get_twocol_bool_row("mcqbool" + str(i))
        for i in range(1, N_MULTIPLERESPONSE + 1):
            h += self.get_twocol_bool_row("multipleresponse" + str(i))
        for i in range(1, N_BOOLTEXT + 1):
            h += self.get_twocol_bool_row("booltext" + str(i))
        for i in range(1, N_BOOLIMAGE + 1):
            h += self.get_twocol_bool_row("boolimage" + str(i))
        for i in range(1, N_PICKER + 1):
            h += self.get_twocol_val_row("picker" + str(i))
        for i in range(1, N_SLIDER + 1):
            h += self.get_twocol_val_row("slider" + str(i))
        h += self.get_twocol_string_row("mcqtext_1a")
        h += self.get_twocol_string_row("mcqtext_1b")
        h += self.get_twocol_string_row("mcqtext_2a")
        h += self.get_twocol_string_row("mcqtext_2b")
        h += self.get_twocol_string_row("mcqtext_3a")
        h += self.get_twocol_string_row("mcqtext_3b")
        h += self.get_twocol_string_row("typedvar_text")
        h += self.get_twocol_string_row("typedvar_text_multiline")
        h += self.get_twocol_string_row("typedvar_text_rich")
        h += self.get_twocol_val_row("typedvar_int")
        h += self.get_twocol_val_row("typedvar_real")
        h += self.get_twocol_val_row("date_only")
        h += self.get_twocol_val_row("date_time")
        h += self.get_twocol_val_row("thermometer")
        h += self.get_twocol_string_row("diagnosticcode_code")
        h += self.get_twocol_string_row("diagnosticcode_description")
        h += self.get_twocol_string_row("diagnosticcode2_code")
        h += self.get_twocol_string_row("diagnosticcode2_description")
        h += self.get_twocol_picture_row(self.photo, "photo")
        h += self.get_twocol_picture_row(self.canvas, "canvas")
        h += self.get_twocol_picture_row(self.canvas2, "canvas2")
        h += """
            </table>

            <div>
                In addition to the data (above), this task demonstrates
                HTML/CSS styles used in the CamCOPS views.
            </div>

            <h1>Header 1</h1>
            <h2>Header 2</h2>
            <h3>Header 3</h3>

            <div>
                Plain div with <sup>superscript</sup> and <sub>subscript</sub>.
                <br>
                Answers look like this: """ + answer("Answer") + """<br>
                Missing answers look liks this: """ + answer(None) + """<br>
            </div>
        """
        h += divtest("badidpolicy_mild")
        h += divtest("badidpolicy_severe")
        h += divtest("clinician")
        h += divtest("copyright")
        h += divtest("error")
        h += divtest("explanation")
        h += divtest("footnotes")
        h += divtest("formtitle")
        h += divtest("green")
        h += divtest("heading")
        h += divtest("important")
        h += divtest("incomplete")
        h += divtest("indented")
        h += divtest("live_on_tablet")
        h += divtest("navigation")
        h += divtest("office")
        h += divtest("patient")
        h += divtest("respondent")
        h += divtest("smallprint")
        h += divtest("specialnote")
        h += divtest("subheading")
        h += divtest("summary")
        h += divtest("superuser")
        h += divtest("taskheader")
        h += divtest("trackerheader")
        h += divtest("tracker_all_consistent")
        h += divtest("warning")
        h += """
            <table>
                <tr>
                    <th>Standard table heading; column 1</th><th>Column 2</th>
                </tr>
                <tr>
                    <td>Standard table row; column 1</td><td>Column 2</td>
                </tr>
            </table>

            <div>Inlined <code>code looks like this</code>.

            <div>There are some others, too.</div>
        """
        return h
