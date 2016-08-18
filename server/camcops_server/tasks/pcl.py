#!/usr/bin/env python3
# pcl.py

"""
    Copyright (C) 2012-2016 Rudolf Cardinal (rudolf@pobox.com).
    Department of Psychiatry, University of Cambridge.
    Funded by the Wellcome Trust.

    This file is part of CamCOPS.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from typing import List

from ..cc_modules.cc_db import repeat_fieldname, repeat_fieldspec
from ..cc_modules.cc_html import (
    answer,
    get_yes_no,
    subheading_spanning_two_columns,
    tr,
    tr_qa,
)
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
)


# =============================================================================
# PCL
# =============================================================================

# -----------------------------------------------------------------------------
# PCL: common class
# -----------------------------------------------------------------------------
# This derives from object, not Task (so the base class doesn't appear in the
# main task list itself), and serves as a mixin for other classes.
# As a result, it calls "self" methods that it doesn't actually possess.

class PclCommon(object):
    NQUESTIONS = 17
    CORE_FIELDSPECS = repeat_fieldspec(
        "q", 1, NQUESTIONS, min=1, max=5,
        comment_fmt="Q{n} ({s}) (1 not at all - 5 extremely)",
        comment_strings=[
            "disturbing memories/thoughts/images",
            "disturbing dreams",
            "reliving",
            "upset at reminders",
            "physical reactions to reminders",
            "avoid thinking/talking/feelings relating to experience",
            "avoid activities/situations because they remind",
            "trouble remembering important parts of stressful event",
            "loss of interest in previously enjoyed activities",
            "feeling distant/cut off from people",
            "feeling emotionally numb",
            "feeling future will be cut short",
            "hard to sleep",
            "irritable",
            "difficulty concentrating",
            "super alert/on guard",
            "jumpy/easily startled",
        ]
    )
    TASK_FIELDS = []
    TASK_TYPE = "?"

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def total_score(self) -> int:
        return self.sum_fields(repeat_fieldname("q", 1, self.NQUESTIONS))

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="PCL total score",
            axis_label="Total score (17-85)",
            axis_min=16.5,
            axis_max=85.5
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="PCL total score {}".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (17-85)"),
            dict(name="num_symptomatic", cctype="INT",
                 value=self.num_symptomatic(),
                 comment="Total number of symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_B", cctype="INT",
                 value=self.num_symptomatic_b(),
                 comment="Number of group B symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_C", cctype="INT",
                 value=self.num_symptomatic_c(),
                 comment="Number of group C symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="num_symptomatic_D", cctype="INT",
                 value=self.num_symptomatic_d(),
                 comment="Number of group D symptoms considered symptomatic "
                 "(meaning scoring 3 or more)"),
            dict(name="ptsd", cctype="BOOL", value=self.ptsd(),
                 comment="Meets DSM-IV criteria for PTSD"),
        ]

    def get_num_symptomatic(self, first: int, last: int) -> int:
        n = 0
        for i in range(first, last + 1):
            value = getattr(self, "q" + str(i))
            if value is not None and value >= 3:
                n += 1
        return n

    def num_symptomatic(self) -> int:
        return self.get_num_symptomatic(1, self.NQUESTIONS)

    def num_symptomatic_b(self) -> int:
        return self.get_num_symptomatic(1, 5)

    def num_symptomatic_c(self) -> int:
        return self.get_num_symptomatic(6, 12)

    def num_symptomatic_d(self) -> int:
        return self.get_num_symptomatic(13, 17)

    def ptsd(self) -> bool:
        num_symptomatic_b = self.num_symptomatic_b()
        num_symptomatic_c = self.num_symptomatic_c()
        num_symptomatic_d = self.num_symptomatic_d()
        return num_symptomatic_b >= 1 and num_symptomatic_c >= 3 and \
            num_symptomatic_d >= 2

    def get_task_html(self) -> str:
        tasktype = self.TASK_TYPE
        score = self.total_score()
        num_symptomatic = self.num_symptomatic()
        num_symptomatic_b = self.num_symptomatic_b()
        num_symptomatic_c = self.num_symptomatic_c()
        num_symptomatic_d = self.num_symptomatic_d()
        ptsd = self.ptsd()
        answer_dict = {None: None}
        for option in range(1, 6):
            answer_dict[option] = str(option) + " – " + \
                WSTRING("pcl_option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr_qa("{} (17–85)".format(WSTRING("total_score")),
                   score)
        h += tr("Number symptomatic <sup>[1]</sup>: B, C, D (total)",
                answer(num_symptomatic_b) + ", " +
                answer(num_symptomatic_c) + ", " +
                answer(num_symptomatic_d) +
                " (" + answer(num_symptomatic) + ")")
        h += tr_qa(WSTRING("pcl_dsm_criteria_met") + " <sup>[2]</sup>",
                   get_yes_no(ptsd))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """
        if tasktype == "S":
            h += tr_qa(WSTRING("pcl_s_event_s"), self.event)
            h += tr_qa(WSTRING("pcl_s_eventdate_s"), self.eventdate)
        for q in range(1, self.NQUESTIONS + 1):
            if q == 1 or q == 6 or q == 13:
                section = "B" if q == 1 else ("C" if q == 6 else "D")
                h += subheading_spanning_two_columns(
                    "DSM section {}".format(section)
                )
            h += tr_qa(
                WSTRING("pcl_q" + str(q) + "_s"),
                get_from_dict(answer_dict, getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Questions with scores ≥3 are considered symptomatic.
                [2] ≥1 ‘B’ symptoms and ≥3 ‘C’ symptoms and
                    ≥2 ‘D’ symptoms.
            </div>
        """
        return h


# -----------------------------------------------------------------------------
# PCL-C
# -----------------------------------------------------------------------------

class PclC(PclCommon, Task):
    tablename = "pclc"
    shortname = "PCL-C"
    longname = "PTSD Checklist, Civilian version"
    fieldspecs = PclCommon.CORE_FIELDSPECS

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    TASK_TYPE = "C"


# -----------------------------------------------------------------------------
# PCL-M
# -----------------------------------------------------------------------------

class PclM(PclCommon, Task):
    tablename = "pclm"
    shortname = "PCL-M"
    longname = "PTSD Checklist, Military version"
    fieldspecs = PclCommon.CORE_FIELDSPECS

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    TASK_TYPE = "M"


# -----------------------------------------------------------------------------
# PCL-S
# -----------------------------------------------------------------------------

class PclS(PclCommon, Task):
    tablename = "pcls"
    shortname = "PCL-S"
    longname = "PTSD Checklist, Stressor-specific version"
    fieldspecs = PclCommon.CORE_FIELDSPECS + [
        dict(name="event", cctype="TEXT",
             comment="Traumatic event"),
        dict(name="eventdate", cctype="TEXT",
             comment="Date of traumatic event (free text)"),
    ]

    TASK_FIELDS = [x["name"] for x in fieldspecs]
    TASK_TYPE = "S"