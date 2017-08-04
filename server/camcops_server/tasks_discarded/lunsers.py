#!/usr/bin/env python
# camcops_server/tasks_discarded/lunsers.py

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

from typing import Dict, List

from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import get_from_dict, Task
from ..cc_modules.cc_trackerhelpers import TrackerInfo


# =============================================================================
# LUNSERS
# =============================================================================

class Lunsers(Task):
    tablename = "lunsers"
    shortname = "LUNSERS"
    longname = "Liverpool University Neuroleptic Side Effect Rating Scale"
    provides_trackers = True

    NQUESTIONS = 51
    list_epse = [19, 29, 34, 37, 40, 43, 48]
    list_anticholinergic = [6, 10, 32, 38, 51]
    list_allergic = [1, 35, 47, 49]
    list_miscellaneous = [5, 22, 39, 44]
    list_psychic = [2, 4, 9, 14, 18, 21, 23, 26, 31, 41]
    list_otherautonomic = [15, 16, 20, 27, 36]
    list_hormonal_female = [7, 13, 17, 24, 46, 50]
    list_hormonal_male = [7, 17, 24, 46]
    list_redherrings = [3, 8, 11, 12, 25, 28, 30, 33, 42, 45]

    fieldspecs = repeat_fieldspec("q", 1, NQUESTIONS)

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="LUNSERS total score",
            axis_label="Total score (out of {})".format(self.max_score()),
            axis_min=-0.5,
            axis_max=0.5 + self.max_score()
        )]

    def get_summaries(self) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(name="total", 
                           coltype=Integer(),
                           value=self.total_score(),
                           comment="Total score"),
        ]

    @staticmethod
    def get_fieldlist(group) -> List[str]:
        return ["q" + str(q) for q in group]

    def get_relevant_fieldlist(self) -> List[str]:
        qnums = range(1, self.NQUESTIONS + 1)
        if not self.is_female():
            qnums.remove(13)
            qnums.remove(50)
        return ["q" + str(q) for q in qnums]

    def is_complete(self) -> bool:
        return self.are_all_fields_complete(self.get_relevant_fieldlist())

    def total_score(self) -> int:
        return self.sum_fields(self.get_relevant_fieldlist())

    def group_score(self, qnums: List[int]) -> int:
        return self.sum_fields(self.get_fieldlist(qnums))

    @staticmethod
    def get_subheading(subtitle: str, score: int, max_score: int) -> str:
        return """
            <tr class="subheading">
                <td>{}</td><td><i><b>{}</b> / {}</i></td>
            </tr>
        """.format(
            subtitle,
            score,
            max_score
        )

    def get_row(self, q: int, answer_dict: Dict) -> str:
        return """<tr><td>{}</td><td><b>{}</b></td></tr>""".format(
            "Q" + str(q) + " — " + self.wxstring("q" + str(q)),
            get_from_dict(answer_dict, getattr(self, "q" + str(q)))
        )

    def get_group_html(self,
                       qnums: List[int],
                       subtitle: str,
                       answer_dict: Dict) -> str:
        h = self.get_subheading(
            subtitle,
            self.group_score(qnums),
            len(qnums) * 4
        )
        for q in qnums:
            h += self.get_row(q, answer_dict)
        return h

    def max_score(self) -> int:
        return 204 if self.is_female() else 196

    def get_task_html(self) -> str:
        score = self.total_score()

        answer_dict = {None: "?"}
        for option in range(0, 5):
            answer_dict[option] = self.wxstring("option" + str(option))
        h = """
            <div class="summary">
                <table class="summary">
                    {}
                    <tr><td>{}</td><td><b>{}</b> / {}</td></tr>
                </table>
            </div>
            <div class="explanation">
                Ratings pertain to the past month.
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="70%">Question</th>
                    <th width="30%">Answer</th>
                </tr>
        """.format(
            self.get_is_complete_tr(),
            wappstring("total_score"), score, self.max_score()
        )
        h += self.get_group_html(self.list_epse,
                                 self.wxstring("group_epse"),
                                 answer_dict)
        h += self.get_group_html(self.list_anticholinergic,
                                 self.wxstring("group_anticholinergic"),
                                 answer_dict)
        h += self.get_group_html(self.list_allergic,
                                 self.wxstring("group_allergic"),
                                 answer_dict)
        h += self.get_group_html(self.list_miscellaneous,
                                 self.wxstring("group_miscellaneous"),
                                 answer_dict)
        h += self.get_group_html(self.list_psychic,
                                 self.wxstring("group_psychic"),
                                 answer_dict)
        h += self.get_group_html(self.list_otherautonomic,
                                 self.wxstring("group_otherautonomic"),
                                 answer_dict)
        if self.is_female():
            h += self.get_group_html(self.list_hormonal_female,
                                     self.wxstring("group_hormonal") + " (" +
                                     wappstring("female") + ")",
                                     answer_dict)
        else:
            h += self.get_group_html(self.list_hormonal_male,
                                     self.wxstring("group_hormonal") + " (" +
                                     wappstring("male") + ")",
                                     answer_dict)
        h += self.get_group_html(self.list_redherrings,
                                 self.wxstring("group_redherrings"),
                                 answer_dict)
        h += """
            </table>
        """
        return h
