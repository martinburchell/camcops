#!/usr/bin/env python3
# smast.py

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

from ..cc_modules.cc_db import repeat_fieldspec
from ..cc_modules.cc_html import answer, tr, tr_qa
from ..cc_modules.cc_string import WSTRING
from ..cc_modules.cc_task import (
    CtvInfo,
    CTV_INCOMPLETE,
    get_from_dict,
    Task,
    TrackerInfo,
    TrackerLabel,
)


# =============================================================================
# SMAST
# =============================================================================

class Smast(Task):
    NQUESTIONS = 13

    tablename = "smast"
    shortname = "SMAST"
    longname = "Short Michigan Alcohol Screening Test"
    fieldspecs = repeat_fieldspec(
        "q", 1, NQUESTIONS, "CHAR", pv=['Y', 'N'],
        comment_fmt="Q{n}: {s} (Y or N)",
        comment_strings=[
            "believe you are a normal drinker",
            "near relative worries/complains",
            "feel guilty",
            "friends/relative think you are a normal drinker",
            "stop when you want to",
            "ever attended Alcoholics Anonymous",
            "problems with close relative",
            "trouble at work",
            "neglected obligations for >=2 days",
            "sought help",
            "hospitalized",
            "arrested for drink-driving",
            "arrested for other drunken behaviour",
        ]
    )

    TASK_FIELDS = [x["name"] for x in fieldspecs]

    def get_trackers(self) -> List[TrackerInfo]:
        return [TrackerInfo(
            value=self.total_score(),
            plot_label="SMAST total score",
            axis_label="Total score (out of 13)",
            axis_min=-0.5,
            axis_max=13.5,
            horizontal_lines=[
                2.5,
                1.5,
            ],
            horizontal_labels=[
                TrackerLabel(4, WSTRING("smast_problem_probable")),
                TrackerLabel(2, WSTRING("smast_problem_possible")),
                TrackerLabel(0.75, WSTRING("smast_problem_unlikely")),
            ]
        )]

    def get_clinical_text(self) -> List[CtvInfo]:
        if not self.is_complete():
            return CTV_INCOMPLETE
        return [CtvInfo(
            content="SMAST total score {}/13 ({})".format(
                self.total_score(), self.likelihood())
        )]

    def get_summaries(self):
        return [
            self.is_complete_summary_field(),
            dict(name="total", cctype="INT", value=self.total_score(),
                 comment="Total score (/13)"),
            dict(name="likelihood", cctype="TEXT",
                 value=self.likelihood(),
                 comment="Likelihood of problem"),
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
        if q == 1 or q == 4 or q == 5:
            return 0 if value == yes else 1
        else:
            return 1 if value == yes else 0

    def total_score(self) -> int:
        total = 0
        for q in range(1, self.NQUESTIONS + 1):
            total += self.get_score(q)
        return total

    def likelihood(self) -> str:
        score = self.total_score()
        if score >= 3:
            return WSTRING("smast_problem_probable")
        elif score >= 2:
            return WSTRING("smast_problem_possible")
        else:
            return WSTRING("smast_problem_unlikely")

    def get_task_html(self) -> str:
        score = self.total_score()
        likelihood = self.likelihood()
        main_dict = {
            None: None,
            "Y": WSTRING("Yes"),
            "N": WSTRING("No")
        }
        h = """
            <div class="summary">
                <table class="summary">
        """
        h += self.get_is_complete_tr()
        h += tr(WSTRING("total_score"), answer(score) + " / 13")
        h += tr_qa(WSTRING("smast_problem_likelihood") + " <sup>[1]</sup>",
                   likelihood)
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
                WSTRING("smast_q" + str(q)),
                answer(get_from_dict(main_dict, getattr(self, "q" + str(q)))) +
                " — " + str(self.get_score(q))
            )
        h += """
            </table>
            <div class="footnotes">
                [1] Total score ≥3 probable, ≥2 possible, 0–1 unlikely.
            </div>
        """
        return h