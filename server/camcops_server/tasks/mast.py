#!/usr/bin/env python
# mast.py

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

from typing import List

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, get_yes_no, tr, tr_qa
from ..cc_modules.cc_string import wappstring
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    LabelAlignment,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# MAST
# =============================================================================

class Mast(Task):
    NQUESTIONS = 24

    tablename = "mast"
    shortname = "MAST"
    longname = "Michigan Alcohol Screening Test"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}: {s} (Y or N)",
        comment_strings=[
            "feel you are a normal drinker",
            "couldn't remember evening before",
            "relative worries/complains",
            "stop drinking after 1-2 drinks",
            "feel guilty",
            "friends/relatives think you are a normal drinker",
            "can stop drinking when you want",
            "attended Alcoholics Anonymous",
            "physical fights",
            "drinking caused problems with relatives",
            "family have sought help",
            "lost friends",
            "trouble at work/school",
            "lost job",
            "neglected obligations for >=2 days",
            "drink before noon often",
            "liver trouble",
            "delirium tremens",
            "sought help",
            "hospitalized",
            "psychiatry admission",
            "clinic visit or professional help",
            "arrested for drink-driving",
            "arrested for other drunk behaviour",
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="MAST total score",
            axis_label="Total score (out of 53)",
            axis_min=-0.5,
            axis_max=53.5,
            horizontal_lines=[12.5],
            horizontal_labels=[
                TrackerLabel(13, "Ross threshold", LabelAlignment.bottom)
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="MAST total score {}/53".format(self.total_score())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/53)"),
            dict(name="exceeds_threshold", cctype="BOOL",
                 value=self.exceeds_ross_threshold(),
                 comment="Exceeds Ross threshold (total score >= 13)"),
        ]

    def is_complete(self) -> bool:
        return (
            self.are_all_fields_complete(self.TASK_FIELDS) and
            self.field_contents_valid()
        )

    def get_score(self, q: int) -> int:
        yes = "Y"
        value = getattr(self, "q" + str(q))
        if value is None:
            return 0
        if q == 1 or q == 4 or q == 6 or q == 7:
            presence = 0 if value == yes else 1
        else:
            presence = 1 if value == yes else 0
        if q == 3 or q == 5 or q == 9 or q == 16:
            points = 1
        elif q == 8 or q == 19 or q == 20:
            points = 5
        else:
            points = 2
        return points * presence

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def exceeds_ross_threshold(self) -> bool:
        score = self.total_score()
        return score >= 13

    def get_task_html(self) -> str:
        score = self.total_score()
        exceeds_threshold = self.exceeds_ross_threshold()
        main_dict = {
            None: None,
            "Y": wappstring("yes"),
            "N": wappstring("no")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """ + self.get_is_complete_tr()
        h += tr(wappstring("total_score"), answer(score) + " / 53")
        h += tr_qa(self.wxstring("exceeds_threshold"),
                   get_yes_no(exceeds_threshold))
        h += """
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="80%">Question</th>
                    <th width="20%">Answer</th>
                </tr>
        """
        for q in range(1, self.NQUESTIONS + 1):
            h += tr(
                self.wxstring("q" + str(q)),
                (
                    answer(get_from_dict(main_dict,
                                         getattr(self, "q" + str(q)))) +
                    answer(" — " + str(self.get_score(q)))
                )
            )
        h += """
            </table>
        """
        return h
