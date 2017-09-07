#!/usr/bin/env python
# camcops_server/tasks/dad.py

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

from typing import Any, Dict, Iterable, List, Tuple, Type

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.sqltypes import Integer

from ..cc_modules.cc_constants import DATA_COLLECTION_UNLESS_UPGRADED_DIV
from ..cc_modules.cc_html import (
    answer,
    subheading_spanning_two_columns,
    tr,
)
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqla_coltypes import CamcopsColumn, PermittedValueChecker
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_summaryelement import SummaryElement
from ..cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
    TaskHasRespondentMixin,
)

YES = 1
NO = 0
NA = -99
YN_NA_CHECKER = PermittedValueChecker(permitted_values=[YES, NO, NA])


# =============================================================================
# DAD
# =============================================================================

class DadMetaclass(DeclarativeMeta):
    # noinspection PyInitNewSignature
    def __init__(cls: Type['Dad'],
                 name: str,
                 bases: Tuple[Type, ...],
                 classdict: Dict[str, Any]) -> None:
        explan = " ({} yes, {} no, {} not applicable)".format(YES, NO, NA)
        for colname in cls.ITEMS:
            setattr(
                cls,
                colname,
                CamcopsColumn(colname, Integer,
                              permitted_value_checker=YN_NA_CHECKER,
                              comment=colname + explan)
            )
        super().__init__(name, bases, classdict)


class Dad(TaskHasPatientMixin, TaskHasRespondentMixin, TaskHasClinicianMixin,
          Task,
          metaclass=DadMetaclass):
    __tablename__ = "dad"
    shortname = "DAD"
    longname = "Disability Assessment for Dementia"

    GROUPS = [
        "hygiene",
        "dressing",
        "continence",
        "eating",
        "mealprep",
        "telephone",
        "outing",
        "finance",
        "medications",
        "leisure"
    ]
    ITEMS = [
        "hygiene_init_wash",
        "hygiene_init_teeth",
        "hygiene_init_hair",
        "hygiene_plan_wash",
        "hygiene_exec_wash",
        "hygiene_exec_hair",
        "hygiene_exec_teeth",

        "dressing_init_dress",
        "dressing_plan_clothing",
        "dressing_plan_order",
        "dressing_exec_dress",
        "dressing_exec_undress",

        "continence_init_toilet",
        "continence_exec_toilet",

        "eating_init_eat",
        "eating_plan_utensils",
        "eating_exec_eat",

        "mealprep_init_meal",
        "mealprep_plan_meal",
        "mealprep_exec_meal",

        "telephone_init_phone",
        "telephone_plan_dial",
        "telephone_exec_conversation",
        "telephone_exec_message",

        "outing_init_outing",
        "outing_plan_outing",
        "outing_exec_reach_destination",
        "outing_exec_mode_transportation",
        "outing_exec_return_with_shopping",

        "finance_init_interest",
        "finance_plan_pay_bills",
        "finance_plan_organise_correspondence",
        "finance_exec_handle_money",

        "medications_init_medication",
        "medications_exec_take_medications",

        "leisure_init_interest_leisure",
        "leisure_init_interest_chores",
        "leisure_plan_chores",
        "leisure_exec_complete_chores",
        "leisure_exec_safe_at_home"
    ]

    def get_summaries(self, req: CamcopsRequest) -> List[SummaryElement]:
        d = self.get_score_dict()
        s = [self.is_complete_summary_field()]
        for item in d:
            s.extend([
                SummaryElement(name=item + "_n",
                               coltype=Integer(),
                               value=d[item][0],
                               comment=item + " (numerator)"),
                SummaryElement(name=item + "_d",
                               coltype=Integer(),
                               value=d[item][1],
                               comment=item + " (denominator)"),
            ])
        return s

    # noinspection PyMethodOverriding
    @staticmethod
    def is_complete() -> bool:
        return True

    @classmethod
    def get_items_activity(cls, activity: str) -> List[str]:
        return [item for item in cls.ITEMS if item.startswith(activity)]

    @classmethod
    def get_items_activities(cls, activities: Iterable[str]) -> List[str]:
        return [item for item in cls.ITEMS
                if any(item.startswith(activity) for activity in activities)]

    @classmethod
    def get_items_phase(cls, phase: str) -> List[str]:
        return [item for item in cls.ITEMS if phase in item]

    def get_score(self, fields: List[str]) -> Tuple[int, int]:
        score = self.count_where(fields, [YES])
        possible = self.count_wherenot(fields, [None, NA])
        return score, possible

    def get_score_dict(self) -> Dict:
        total = self.get_score(self.ITEMS)
        hygiene = self.get_score(self.get_items_activity('hygiene'))
        dressing = self.get_score(self.get_items_activity('dressing'))
        continence = self.get_score(self.get_items_activity('continence'))
        eating = self.get_score(self.get_items_activity('eating'))
        badl = self.get_score(self.get_items_activities(
            ['hygiene', 'dressing', 'continence', 'eating']))
        mealprep = self.get_score(self.get_items_activity('mealprep'))
        telephone = self.get_score(self.get_items_activity('telephone'))
        outing = self.get_score(self.get_items_activity('outing'))
        finance = self.get_score(self.get_items_activity('finance'))
        medications = self.get_score(self.get_items_activity('medications'))
        leisure = self.get_score(self.get_items_activity('leisure'))
        iadl = self.get_score(self.get_items_activities(
            ['mealprep', 'telephone', 'outing', 'finance',
             'medications', 'leisure']))
        initiation = self.get_score(self.get_items_phase('init'))
        planning = self.get_score(self.get_items_phase('plan'))
        execution = self.get_score(self.get_items_phase('exec'))
        # n for numerator, d for denominator
        return dict(
            total=total,
            hygiene=hygiene,
            dressing=dressing,
            continence=continence,
            eating=eating,
            badl=badl,
            mealprep=mealprep,
            telephone=telephone,
            outing=outing,
            finance=finance,
            medications=medications,
            leisure=leisure,
            iadl=iadl,
            initiation=initiation,
            planning=planning,
            execution=execution,
        )

    @staticmethod
    def report_score(score_tuple: Tuple[int, int]) -> str:
        return "{} / {}".format(answer(score_tuple[0]), score_tuple[1])

    def report_answer(self, field: str) -> str:
        value = getattr(self, field)
        if value == YES:
            text = "Yes (1)"
        elif value == NO:
            text = "No (0)"
        elif value == NA:
            text = "N/A"
        else:
            text = None
        return answer(text)

    def get_task_html(self, req: CamcopsRequest) -> str:
        d = self.get_score_dict()
        h = """
            <div class="summary">
                <table class="summary">
                    {complete_tr}
                    <tr><td>Total</td><td>{total}</td></tr>
                    <tr><td>Activity: hygiene</td><td>{hygiene}</td></tr>
                    <tr><td>Activity: dressing</td><td>{dressing}</td></tr>
                    <tr><td>Activity: continence</td><td>{continence}</td></tr>
                    <tr><td>Activity: eating</td><td>{eating}</td></tr>
                    <tr>
                        <td>Basic activities of daily living (BADLs) (hygiene,
                        dressing, continence, eating)</td>
                        <td>{badl}</td>
                    </tr>
                    <tr>
                        <td>Activity: meal preparation</td><td>{mealprep}</td>
                    </tr>
                    <tr><td>Activity: telephone</td><td>{telephone}</td></tr>
                    <tr><td>Activity: outings</td><td>{outing}</td></tr>
                    <tr><td>Activity: finance</td><td>{finance}</td></tr>
                    <tr>
                        <td>Activity: medications</td><td>{medications}</td>
                    </tr>
                    <tr><td>Activity: leisure</td><td>{leisure}</td></tr>
                    <tr>
                        <td>Instrumental activities of daily living (IADLs)
                        (meal prep., telephone, outings, finance, medications,
                        leisure)</td>
                        <td>{iadl}</td>
                    </tr>
                    <tr>
                        <td>Phase: initiation</td>
                        <td>{initiation}</td>
                    </tr>
                    <tr>
                        <td>Phase: planning/organisation</td>
                        <td>{planning}</td>
                    </tr>
                    <tr>
                        <td>Phase: execution/performance</td>
                        <td>{execution}</td>
                    </tr>
                </table>
            </div>
            <table class="taskdetail">
                <tr>
                    <th width="50%">Question (I = initiation, P = planning,
                        E = execution)</th>
                    <th width="50%">Answer</th>
                </tr>
        """.format(
            complete_tr=self.get_is_complete_tr(req),
            total=self.report_score(d['total']),
            hygiene=self.report_score(d['hygiene']),
            dressing=self.report_score(d['dressing']),
            continence=self.report_score(d['continence']),
            eating=self.report_score(d['eating']),
            badl=self.report_score(d['badl']),
            mealprep=self.report_score(d['mealprep']),
            telephone=self.report_score(d['telephone']),
            outing=self.report_score(d['outing']),
            finance=self.report_score(d['finance']),
            medications=self.report_score(d['medications']),
            leisure=self.report_score(d['leisure']),
            iadl=self.report_score(d['iadl']),
            initiation=self.report_score(d['initiation']),
            planning=self.report_score(d['planning']),
            execution=self.report_score(d['execution']),
        )
        for group in self.GROUPS:
            h += subheading_spanning_two_columns(self.wxstring(req, group))
            for item in self.ITEMS:
                if not item.startswith(group):
                    continue
                q = self.wxstring(req, item)
                if '_init_' in item:
                    q += " (I)"
                elif '_plan_' in item:
                    q += " (P)"
                elif '_exec_' in item:
                    q += " (E)"
                else:
                    # Shouldn't happen
                    q += " (?)"
                h += tr(q, self.report_answer(item))
        h += """
            </table>
        """ + DATA_COLLECTION_UNLESS_UPGRADED_DIV
        return h
