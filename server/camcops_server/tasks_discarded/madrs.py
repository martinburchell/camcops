#!/usr/bin/env python
# camcops_server/tasks_discarded/madrs.py

"""
===============================================================================

    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

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

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text

from camcops_server.cc_modules.cc_db import add_multiple_columns
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_summaryelement import SummaryElement
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)
from camcops_server.cc_modules.cc_trackerhelpers import (
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# MADRS
# =============================================================================

class MadrsMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Madrs'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(cls, "q", 1, cls.NQUESTIONS)
        super().__init__(name, bases, classdict)


class Madrs(TaskHasPatientMixin, TaskHasClinicianMixin, Task,
            metaclass=MadrsMetaclass):
    __tablename__ = "madrs"
    shortname = "MADRS"
    longname = "Montgomery–Åsberg Depression Rating Scale"
    provides_trackers = True

    period_rated = Column("period_rated", Text)

    NQUESTIONS = 10
    QFIELDS = strseq("q", 1, NQUESTIONS)
    TASK_FIELDS = QFIELDS + ["period_rated"]
    MAX_TOTAL = 60

    def get_trackers(self, req: CamcopsRequest) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="MADRS total score",
            axis_label="Total score (out of {})".format(self.MAX_TOTAL),
            axis_min=-0.5,
            axis_max=self.MAX_TOTAL + 0.5,
            horizontal_lines=[
                33.5,
                19.5,
                6.5,
            ],
            horizontal_labels=[
                TrackerLabel(35, req.wappstring("severe")),
                TrackerLabel(25, req.wappstring("moderate")),
                TrackerLabel(14, req.wappstring("mild")),
                TrackerLabel(3, req.wappstring("normal"))
            ]
        )]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return self.standard_task_summary_fields() + [
            SummaryElement(name="total",
                           coltype=Integer(),
                           value=self.total_score()),
        ]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def total_score(self) -> int:
        return self.sum_fields(self.QFIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        score = self.total_score()
        if score > 34:
            category = req.wappstring("severe")
        elif score >= 20:
            category = req.wappstring("moderate")
        elif score >= 7:
            category = req.wappstring("mild")
        else:
            category = req.wappstring("normal")
        answer_dicts = []
        for q in range(1, self.NQUESTIONS + 1):
            d = {None: "?"}
            for option in range(0, 7):
                if option == 1 or option == 3 or option == 5:
                    d[option] = option
                else:
                    d[option] = self.wxstring(req, "q" + str(q) + "_option" +
                                              str(option))
            answer_dicts.append(d)
        h = """
            <div class="summary">
                <table class="summary">
                    {is_complete}
                    <tr>
                        <td>{total_score_str}</td>
                        <td><b>{score}</b> / {max_total}</td>
                    </tr>
                    <tr>
                        <td>{category_str} <sup>[1]</sup></td>
                        <td><b>{category}</b>
                    </tr>
                </table>
            </div>
            <div class="explanation">
                Ratings are from 0–6 (0 none, 6 extreme problem).
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="30%">Question</th>
                    <th width="70%">Answer</th>
                </tr>
                <tr>
                    <td>{q_period_rated}</td>
                    <td><b>{period_rated}</b></td>
                </tr>
        """.format(
            is_complete=self.get_is_complete_tr(req),
            total_score_str=req.wappstring("total_score"),
            score=score,
            max_total=self.MAX_TOTAL,
            category_str=req.wappstring("category"),
            category=category,
            q_period_rated=self.wxstring(req, "q_period_rated"),
            period_rated=self.period_rated,
        )
        for q in range(1, self.NQUESTIONS + 1):
            h += """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
                self.wxstring(req, "madrs_q" + str(q) + "_s"),
                get_from_dict(answer_dicts[q - 1], getattr(self, "q" + str(q)))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Total score &gt;34 severe, &ge;20 moderate, &ge;7 mild,
                &lt;7 normal. (Hermann et al. 1998, PubMed ID 9506602.)
            </div>
        """
        return h
