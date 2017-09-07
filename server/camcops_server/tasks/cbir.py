#!/usr/bin/env python
# camcops_server/tasks/cbir.py

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

from typing import Any, Dict, List, Optional, Tuple, Type

from cardinal_pythonlib.stringfunc import strseq
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Float, Integer, UnicodeText

from ..cc_modules.cc_db import add_multiple_columns
from ..cc_modules.cc_html import (
    answer,
    get_yes_no,
    subheading_spanning_three_columns,
    tr,
)
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqla_coltypes import BIT_CHECKER, CamcopsColumn
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import (
    get_from_dict,
    Task,
    TaskHasPatientMixin,
    TaskHasRespondentMixin,
)


# =============================================================================
# CBI-R
# =============================================================================

QUESTION_SNIPPETS = [
    "memory: poor day to day memory",  # 1
    "memory: asks same questions",
    "memory: loses things",
    "memory: forgets familiar names",
    "memory: forgets names of objects",  # 5
    "memory: poor concentration",
    "memory: forgets day",
    "memory: confused in unusual surroundings",
    "everyday: electrical appliances",
    "everyday: writing",  # 10
    "everyday: using telephone",
    "everyday: making hot drink",
    "everyday: money",
    "self-care: grooming",
    "self-care: dressing",  # 15
    "self-care: feeding",
    "self-care: bathing",
    "behaviour: inappropriate humour",
    "behaviour: temper outbursts",
    "behaviour: uncooperative",  # 20
    "behaviour: socially embarrassing",
    "behaviour: tactless/suggestive",
    "behaviour: impulsive",
    "mood: cries",
    "mood: sad/depressed",  # 25
    "mood: restless/agitated",
    "mood: irritable",
    "beliefs: visual hallucinations",
    "beliefs: auditory hallucinations",
    "beliefs: delusions",  # 30
    "eating: sweet tooth",
    "eating: repetitive",
    "eating: increased appetite",
    "eating: table manners",
    "sleep: disturbed at night",  # 35
    "sleep: daytime sleep increased",
    "stereotypy/motor: rigid/fixed opinions",
    "stereotypy/motor: routines",
    "stereotypy/motor: preoccupied with time",
    "stereotypy/motor:  expression/catchphrase",  # 40
    "motivation: less enthusiasm in usual interests",
    "motivation: no interest in new things",
    "motivation: fails to contact friends/family",
    "motivation: indifferent to family/friend concerns",
    "motivation: reduced affection",  # 45
]


class CbiRMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['CbiR'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        add_multiple_columns(
            cls, "frequency", 1, cls.NQUESTIONS,
            comment_fmt="Frequency Q{n}, {s} (0-4, higher worse)",
            minimum=cls.MIN_SCORE, maximum=cls.MAX_SCORE,
            comment_strings=QUESTION_SNIPPETS
        )
        add_multiple_columns(
            cls, "distress", 1, cls.NQUESTIONS,
            comment_fmt="Distress Q{n}, {s} (0-4, higher worse)",
            minimum=cls.MIN_SCORE, maximum=cls.MAX_SCORE,
            comment_strings=QUESTION_SNIPPETS
        )
        super().__init__(name, bases, classdict)


class CbiR(TaskHasPatientMixin, TaskHasRespondentMixin, Task,
           metaclass=CbiRMetaclass):
    __tablename__ = "cbir"
    shortname = "CBI-R"
    longname = "Cambridge Behavioural Inventory, Revised"

    confirm_blanks = CamcopsColumn(
        "confirm_blanks", Integer,
        permitted_value_checker=BIT_CHECKER,
        comment="Respondent confirmed that blanks are deliberate (N/A) "
                "(0/NULL no, 1 yes)"
    )
    comments = Column(
        "comments", UnicodeText,
        comment="Additional comments"
    )

    MIN_SCORE = 0
    MAX_SCORE = 4
    QNUMS_MEMORY = (1, 8)  # tuple: first, last
    QNUMS_EVERYDAY = (9, 13)
    QNUMS_SELF = (14, 17)
    QNUMS_BEHAVIOUR = (18, 23)
    QNUMS_MOOD = (24, 27)
    QNUMS_BELIEFS = (28, 30)
    QNUMS_EATING = (31, 34)
    QNUMS_SLEEP = (35, 36)
    QNUMS_STEREOTYPY = (37, 40)
    QNUMS_MOTIVATION = (41, 45)

    NQUESTIONS = 45
    TASK_FIELDS = (strseq("frequency", 1, NQUESTIONS) +
                   strseq("distress", 1, NQUESTIONS))

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        return [
            self.is_complete_summary_field(),
            SummaryElement(
                name="memory_frequency_pct",
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_MEMORY),
                comment="Memory/orientation: frequency score (% of max)"),
            SummaryElement(
                name="memory_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_MEMORY),
                comment="Memory/orientation: distress score (% of max)"),
            SummaryElement(
                name="everyday_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_EVERYDAY),
                comment="Everyday skills: frequency score (% of max)"),
            SummaryElement(
                name="everyday_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_EVERYDAY),
                comment="Everyday skills: distress score (% of max)"),
            SummaryElement(
                name="selfcare_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_SELF),
                comment="Self-care: frequency score (% of max)"),
            SummaryElement(
                name="selfcare_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_SELF),
                comment="Self-care: distress score (% of max)"),
            SummaryElement(
                name="behaviour_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_BEHAVIOUR),
                comment="Abnormal behaviour: frequency score (% of max)"),
            SummaryElement(
                name="behaviour_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_BEHAVIOUR),
                comment="Abnormal behaviour: distress score (% of max)"),
            SummaryElement(
                name="mood_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_MOOD),
                comment="Mood: frequency score (% of max)"),
            SummaryElement(
                name="mood_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_MOOD),
                comment="Mood: distress score (% of max)"),
            SummaryElement(
                name="beliefs_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_BELIEFS),
                comment="Beliefs: frequency score (% of max)"),
            SummaryElement(
                name="beliefs_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_BELIEFS),
                comment="Beliefs: distress score (% of max)"),
            SummaryElement(
                name="eating_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_EATING),
                comment="Eating habits: frequency score (% of max)"),
            SummaryElement(
                name="eating_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_EATING),
                comment="Eating habits: distress score (% of max)"),
            SummaryElement(
                name="sleep_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_SLEEP),
                comment="Sleep: frequency score (% of max)"),
            SummaryElement(
                name="sleep_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_SLEEP),
                comment="Sleep: distress score (% of max)"),
            SummaryElement(
                name="stereotypic_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_STEREOTYPY),
                comment="Stereotypic and motor behaviours: frequency "
                        "score (% of max)"),
            SummaryElement(
                name="stereotypic_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_STEREOTYPY),
                comment="Stereotypic and motor behaviours: distress "
                        "score (% of max)"),
            SummaryElement(
                name="motivation_frequency_pct", 
                coltype=Float(),
                value=self.frequency_subscore(*self.QNUMS_MOTIVATION),
                comment="Motivation: frequency score (% of max)"),
            SummaryElement(
                name="motivation_distress_pct", 
                coltype=Float(),
                value=self.distress_subscore(*self.QNUMS_MOTIVATION),
                comment="Motivation: distress score (% of max)"),
        ]

    def subscore(self, first: int, last: int, fieldprefix: str) \
            -> Optional[float]:
        score = 0
        n = 0
        for q in range(first, last + 1):
            value = getattr(self, fieldprefix + str(q))
            if value is not None:
                score += value / self.MAX_SCORE
                n += 1
        return 100 * score / n if n > 0 else None

    def frequency_subscore(self, first: int, last: int) -> Optional[float]:
        return self.subscore(first, last, "frequency")

    def distress_subscore(self, first: int, last: int) -> Optional[float]:
        return self.subscore(first, last, "distress")

    def is_complete(self) -> bool:
        if (not self.field_contents_valid() or
                not self.is_respondent_complete()):
            return False
        if self.confirm_blanks:
            return True
        return self.are_all_fields_complete(self.TASK_FIELDS)

    def get_task_html(self, req: CamcopsRequest) -> str:
        freq_dict = {None: None}
        distress_dict = {None: None}
        for a in range(self.MIN_SCORE, self.MAX_SCORE + 1):
            freq_dict[a] = self.wxstring(req, "f" + str(a))
            distress_dict[a] = self.wxstring(req, "d" + str(a))

        heading_memory = self.wxstring(req, "h_memory")
        heading_everyday = self.wxstring(req, "h_everyday")
        heading_selfcare = self.wxstring(req, "h_selfcare")
        heading_behaviour = self.wxstring(req, "h_abnormalbehaviour")
        heading_mood = self.wxstring(req, "h_mood")
        heading_beliefs = self.wxstring(req, "h_beliefs")
        heading_eating = self.wxstring(req, "h_eating")
        heading_sleep = self.wxstring(req, "h_sleep")
        heading_motor = self.wxstring(req, "h_stereotypy_motor")
        heading_motivation = self.wxstring(req, "h_motivation")

        def get_question_rows(first, last):
            html = ""
            for q in range(first, last + 1):
                f = getattr(self, "frequency" + str(q))
                d = getattr(self, "distress" + str(q))
                fa = ("{}: {}".format(f, get_from_dict(freq_dict, f))
                      if f is not None else None)
                da = ("{}: {}".format(d, get_from_dict(distress_dict, d))
                      if d is not None else None)
                html += tr(
                    self.wxstring(req, "q" + str(q)),
                    answer(fa),
                    answer(da),
                )
            return html

        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                </table>
                <table class="summary">
                    <tr>
                        <th>Subscale</th>
                        <th>Frequency (% of max)</th>
                        <th>Distress (% of max)</th>
                    </tr>
                    <tr>
                        <td>{heading_memory}</td>
                        <td>{mem_f}</td>
                        <td>{mem_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_everyday}</td>
                        <td>{everyday_f}</td>
                        <td>{everyday_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_selfcare}</td>
                        <td>{self_f}</td>
                        <td>{self_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_behaviour}</td>
                        <td>{behav_f}</td>
                        <td>{behav_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_mood}</td>
                        <td>{mood_f}</td>
                        <td>{mood_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_beliefs}</td>
                        <td>{beliefs_f}</td>
                        <td>{beliefs_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_eating}</td>
                        <td>{eating_f}</td>
                        <td>{eating_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_sleep}</td>
                        <td>{sleep_f}</td>
                        <td>{sleep_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_motor}</td>
                        <td>{motor_f}</td>
                        <td>{motor_d}</td>
                    </tr>
                    <tr>
                        <td>{heading_motivation}</td>
                        <td>{motivation_f}</td>
                        <td>{motivation_d}</td>
                    </tr>
                </table>
            </div>
            <table class="taskdetail">
                {tr_blanks}
                {tr_comments}
            </table>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question</th>
                    <th width="25%">Frequency (0–4)</th>
                    <th width="25%">Distress (0–4)</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(req),
            heading_memory=heading_memory,
            mem_f=answer(self.frequency_subscore(*self.QNUMS_MEMORY)),
            mem_d=answer(self.distress_subscore(*self.QNUMS_MEMORY)),
            heading_everyday=heading_everyday,
            everyday_f=answer(self.frequency_subscore(*self.QNUMS_EVERYDAY)),
            everyday_d=answer(self.distress_subscore(*self.QNUMS_EVERYDAY)),
            heading_selfcare=heading_selfcare,
            self_f=answer(self.frequency_subscore(*self.QNUMS_SELF)),
            self_d=answer(self.distress_subscore(*self.QNUMS_SELF)),
            heading_behaviour=heading_behaviour,
            behav_f=answer(self.frequency_subscore(*self.QNUMS_BEHAVIOUR)),
            behav_d=answer(self.distress_subscore(*self.QNUMS_BEHAVIOUR)),
            heading_mood=heading_mood,
            mood_f=answer(self.frequency_subscore(*self.QNUMS_MOOD)),
            mood_d=answer(self.distress_subscore(*self.QNUMS_MOOD)),
            heading_beliefs=heading_beliefs,
            beliefs_f=answer(self.frequency_subscore(*self.QNUMS_BELIEFS)),
            beliefs_d=answer(self.distress_subscore(*self.QNUMS_BELIEFS)),
            heading_eating=heading_eating,
            eating_f=answer(self.frequency_subscore(*self.QNUMS_EATING)),
            eating_d=answer(self.distress_subscore(*self.QNUMS_EATING)),
            heading_sleep=heading_sleep,
            sleep_f=answer(self.frequency_subscore(*self.QNUMS_SLEEP)),
            sleep_d=answer(self.distress_subscore(*self.QNUMS_SLEEP)),
            heading_motor=heading_motor,
            motor_f=answer(self.frequency_subscore(*self.QNUMS_STEREOTYPY)),
            motor_d=answer(self.distress_subscore(*self.QNUMS_STEREOTYPY)),
            heading_motivation=heading_motivation,
            motivation_f=answer(
                self.frequency_subscore(*self.QNUMS_MOTIVATION)),
            motivation_d=answer(
                self.distress_subscore(*self.QNUMS_MOTIVATION)),
            tr_blanks=tr(
                "Respondent confirmed that blanks are deliberate (N/A)",
                answer(get_yes_no(req, self.confirm_blanks))),
            tr_comments=tr("Comments",
                           answer(self.comments, default="")),
        )
        h += subheading_spanning_three_columns(heading_memory)
        h += get_question_rows(*self.QNUMS_MEMORY)
        h += subheading_spanning_three_columns(heading_everyday)
        h += get_question_rows(*self.QNUMS_EVERYDAY)
        h += subheading_spanning_three_columns(heading_selfcare)
        h += get_question_rows(*self.QNUMS_SELF)
        h += subheading_spanning_three_columns(heading_behaviour)
        h += get_question_rows(*self.QNUMS_BEHAVIOUR)
        h += subheading_spanning_three_columns(heading_mood)
        h += get_question_rows(*self.QNUMS_MOOD)
        h += subheading_spanning_three_columns(heading_beliefs)
        h += get_question_rows(*self.QNUMS_BELIEFS)
        h += subheading_spanning_three_columns(heading_eating)
        h += get_question_rows(*self.QNUMS_EATING)
        h += subheading_spanning_three_columns(heading_sleep)
        h += get_question_rows(*self.QNUMS_SLEEP)
        h += subheading_spanning_three_columns(heading_motor)
        h += get_question_rows(*self.QNUMS_STEREOTYPY)
        h += subheading_spanning_three_columns(heading_motivation)
        h += get_question_rows(*self.QNUMS_MOTIVATION)
        h += """
            </table>
        """
        return h
