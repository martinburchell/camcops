#!/usr/bin/env python

"""
camcops_server/tasks/perinatalpoem.py

===============================================================================

    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, UnicodeText

from camcops_server.cc_modules.cc_constants import CssClass
from camcops_server.cc_modules.cc_html import (
    get_yes_no_none,
    subheading_spanning_two_columns,
    tr_qa,
)
from camcops_server.cc_modules.cc_request import CamcopsRequest
from camcops_server.cc_modules.cc_task import (
    get_from_dict,
    Task,
)


# =============================================================================
# Perinatal-POEM
# =============================================================================

class PerinatalPoem(Task):
    """
    Server implementation of the Perinatal-POEM task.
    """
    __tablename__ = "perinatal_poem"
    shortname = "Perinatal-POEM"
    longname = "Perinatal Patient-rated Outcome and Experience Measure"
    provides_trackers = False

    # Field names
    FN_QA_RESPONDENT = "qa"
    FN_QB_SERVICE_TYPE = "qb"
    FN_Q1A_MH_FIRST_CONTACT = "q1a"
    FN_Q1B_MH_DISCHARGE = "q1b"
    FN_Q2A_STAFF_DID_NOT_COMMUNICATE = "q2a"
    FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT = "q2b"
    FN_Q2C_HELP_NOT_QUICK_ENOUGH = "q2c"
    FN_Q2D_STAFF_LISTENED = "q2d"
    FN_Q2E_STAFF_DID_NOT_INVOLVE_ME = "q2e"
    FN_Q2F_SERVICE_PROVIDED_INFO = "q2f"
    FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME = "q2g"
    FN_Q2H_STAFF_HELPED_ME_UNDERSTAND = "q2h"
    FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY = "q2i"
    FN_Q2J_STAFF_HELPED_MY_CONFIDENCE = "q2j"
    FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY = "q2k"
    FN_Q2L_I_WOULD_RECOMMEND_SERVICE = "q2l"
    FN_Q3A_UNIT_CLEAN = "q3a"
    FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER = "q3b"
    FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES = "q3c"
    FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY = "q3d"
    FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT = "q3e"
    FN_Q3F_FOOD_NOT_ACCEPTABLE = "q3f"
    FN_GENERAL_COMMENTS = "general_comments"
    FN_FUTURE_PARTICIPATION = "future_participation"
    FN_CONTACT_DETAILS = "contact_details"

    # Response values
    VAL_QA_PATIENT = 1
    VAL_QA_PARTNER_OTHER = 2

    VAL_QB_INPATIENT = 1  # inpatient = MBU = mother and baby unit
    VAL_QB_COMMUNITY = 2

    VAL_Q1_VERY_WELL = 1
    VAL_Q1_WELL = 2
    VAL_Q1_UNWELL = 3
    VAL_Q1_VERY_UNWELL = 4
    VAL_Q1_EXTREMELY_UNWELL = 5
    _MH_KEY = (
        "({vw} very well, {we} well, {un} unwell, "
        "{vu} very unwell, {eu} extremely unwell)".format(
            vw=VAL_Q1_VERY_WELL,
            we=VAL_Q1_WELL,
            un=VAL_Q1_UNWELL,
            vu=VAL_Q1_VERY_UNWELL,
            eu=VAL_Q1_EXTREMELY_UNWELL
        )
    )

    VAL_STRONGLY_AGREE = 1
    VAL_AGREE = 2
    VAL_DISAGREE = 3
    VAL_STRONGLY_DISAGREE = 4
    _AGREE_KEY = (
        "({sa} strongly agree, {ag} agree, "
        "{di} disagree, {sd} strongly disagree)".format(
            sa=VAL_STRONGLY_AGREE,
            ag=VAL_AGREE,
            di=VAL_DISAGREE,
            sd=VAL_STRONGLY_DISAGREE,
        )
    )

    _INPATIENT_ONLY = "[Inpatient services only]"

    YES_INT = 1
    NO_INT = 0

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------
    qa = Column(
        FN_QA_RESPONDENT, Integer,
        comment=(
            "Question A: Is the respondent the patient ({p}) or "
            "other ({o})?".format(p=VAL_QA_PATIENT, o=VAL_QA_PARTNER_OTHER)
        )
    )
    qb = Column(
        FN_QB_SERVICE_TYPE, Integer,
        comment=(
            "Question B: Was the service type inpatient [mother-and-baby "
            "unit, MBU] ({i}) or community ({c})?".format(
                i=VAL_QB_INPATIENT,
                c=VAL_QB_COMMUNITY,
            )
        )
    )

    q1a = Column(
        FN_Q1A_MH_FIRST_CONTACT, Integer,
        comment="Q1A: mental health at first contact {}".format(_MH_KEY)
    )
    q1b = Column(
        FN_Q1B_MH_DISCHARGE, Integer,
        comment="Q1B: mental health at discharge {}".format(_MH_KEY)
    )

    q2a = Column(
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE, Integer,
        comment="Q2a: staff didn't communicate with others "
                "{}".format(_AGREE_KEY)
    )
    q2b = Column(
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT, Integer,
        comment="Q2b: Staff gave right amount of support "
                "{}".format(_AGREE_KEY)
    )
    q2c = Column(
        FN_Q2C_HELP_NOT_QUICK_ENOUGH, Integer,
        comment="Q2c: Help not quick enough after referral "
                "{}".format(_AGREE_KEY)
    )
    q2d = Column(
        FN_Q2D_STAFF_LISTENED, Integer,
        comment="Q2d: Staff listened/understood {}".format(_AGREE_KEY)
    )

    q2e = Column(
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME, Integer,
        comment="Q2e: Staff didn't involve pt enough {}".format(_AGREE_KEY)
    )
    q2f = Column(
        FN_Q2F_SERVICE_PROVIDED_INFO, Integer,
        comment="Q2f: Service provided information {}".format(_AGREE_KEY)
    )
    q2g = Column(
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME, Integer,
        comment="Q2g: Staff not very sensitive to pt {}".format(_AGREE_KEY)
    )
    q2h = Column(
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND, Integer,
        comment="Q2h: Staff helped understanding of illness "
                "{}".format(_AGREE_KEY)
    )

    q2i = Column(
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY, Integer,
        comment="Q2i: Staff not very sensitive to baby {}".format(_AGREE_KEY)
    )
    q2j = Column(
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE, Integer,
        comment="Q2j: Staff helped confidence re baby {}".format(_AGREE_KEY)
    )
    q2k = Column(
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY, Integer,
        comment="Q2k: Service involved others helpfully {}".format(_AGREE_KEY)
    )
    q2l = Column(
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE, Integer,
        comment="Q2l: Would recommend service {}".format(_AGREE_KEY)
    )

    q3a = Column(
        FN_Q3A_UNIT_CLEAN, Integer,
        comment="Q3a: MBU clean {} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )
    q3b = Column(
        FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER, Integer,
        comment="Q3b: MBU not a good place to recover "
                "{} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )
    q3c = Column(
        FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES, Integer,
        comment="Q3c: MBU did not provide helpful activities "
                "{} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )
    q3d = Column(
        FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY, Integer,
        comment="Q3d: MBU a good place for baby to be with pt "
                "{} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )
    q3e = Column(
        FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT, Integer,
        comment="Q3e: MBU supported contact with family/friends "
                "{} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )
    q3f = Column(
        FN_Q3F_FOOD_NOT_ACCEPTABLE, Integer,
        comment="Q3f: Food not acceptable "
                "{} {}".format(_AGREE_KEY, _INPATIENT_ONLY)
    )

    general_comments = Column(
        FN_GENERAL_COMMENTS, UnicodeText,
        comment="General comments"
    )
    future_participation = Column(
        FN_FUTURE_PARTICIPATION, Integer,
        comment="Willing to participate in future studies "
                "({y} yes, {n} no)".format(y=YES_INT, n=NO_INT)
    )
    contact_details = Column(
        FN_CONTACT_DETAILS, UnicodeText,
        comment="Contact details"
    )

    # -------------------------------------------------------------------------
    # Fieldname collections
    # -------------------------------------------------------------------------
    REQUIRED_ALWAYS = [
        FN_QA_RESPONDENT,
        FN_QB_SERVICE_TYPE,
        FN_Q1A_MH_FIRST_CONTACT,
        FN_Q1B_MH_DISCHARGE,
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE,
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT,
        FN_Q2C_HELP_NOT_QUICK_ENOUGH,
        FN_Q2D_STAFF_LISTENED,
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME,
        FN_Q2F_SERVICE_PROVIDED_INFO,
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME,
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND,
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY,
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE,
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY,
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE,
        # not FN_GENERAL_COMMENTS,
        FN_FUTURE_PARTICIPATION,
        # not FN_CONTACT_DETAILS,
    ]
    REQUIRED_INPATIENT = [
        FN_Q3A_UNIT_CLEAN,
        FN_Q3B_UNIT_NOT_GOOD_PLACE_TO_RECOVER,
        FN_Q3C_UNIT_DID_NOT_PROVIDE_ACTIVITIES,
        FN_Q3D_UNIT_GOOD_PLACE_FOR_BABY,
        FN_Q3E_UNIT_SUPPORTED_FAMILY_FRIENDS_CONTACT,
        FN_Q3F_FOOD_NOT_ACCEPTABLE,
    ]
    Q1_FIELDS = [
        FN_Q1A_MH_FIRST_CONTACT,
        FN_Q1B_MH_DISCHARGE,
    ]
    Q2_FIELDS = [
        FN_Q2A_STAFF_DID_NOT_COMMUNICATE,
        FN_Q2B_STAFF_GAVE_RIGHT_SUPPORT,
        FN_Q2C_HELP_NOT_QUICK_ENOUGH,
        FN_Q2D_STAFF_LISTENED,
        FN_Q2E_STAFF_DID_NOT_INVOLVE_ME,
        FN_Q2F_SERVICE_PROVIDED_INFO,
        FN_Q2G_STAFF_NOT_SENSITIVE_TO_ME,
        FN_Q2H_STAFF_HELPED_ME_UNDERSTAND,
        FN_Q2I_STAFF_NOT_SENSITIVE_TO_BABY,
        FN_Q2J_STAFF_HELPED_MY_CONFIDENCE,
        FN_Q2K_SERVICE_INVOLVED_OTHERS_HELPFULLY,
        FN_Q2L_I_WOULD_RECOMMEND_SERVICE,
    ]
    Q3_FIELDS = REQUIRED_INPATIENT

    def was_inpatient(self) -> bool:
        return self.qb == self.VAL_QB_INPATIENT

    def respondent_not_patient(self) -> bool:
        return self.qa == self.VAL_QA_PARTNER_OTHER

    def offering_participation(self) -> bool:
        return self.future_participation == self.YES_INT

    def is_complete(self) -> bool:
        if not self.are_all_fields_complete(self.REQUIRED_ALWAYS):
            return False
        if (self.was_inpatient() and
                not self.are_all_fields_complete(self.REQUIRED_INPATIENT)):
            return False
        if not self.field_contents_valid():
            return False
        return True

    def get_task_html(self, req: CamcopsRequest) -> str:
        def loadvalues(_dict: Dict[int, str], _first: int, _last: int,
                       _xstringprefix: str) -> None:
            for val in range(_first, _last + 1):
                _dict[val] = "{} — {}".format(
                    val,
                    self.wxstring(req, "{}{}".format(_xstringprefix, val))
                )

        respondent_dict = {}  # type: Dict[int, str]
        loadvalues(respondent_dict, self.VAL_QA_PATIENT,
                   self.VAL_QA_PARTNER_OTHER, "qa_a")
        service_dict = {}  # type: Dict[int, str]
        loadvalues(service_dict, self.VAL_QB_INPATIENT,
                   self.VAL_QB_COMMUNITY, "qb_a")
        mh_dict = {}  # type: Dict[int, str]
        loadvalues(mh_dict, self.VAL_Q1_VERY_WELL,
                   self.VAL_Q1_EXTREMELY_UNWELL, "q1_a")
        agree_dict = {}  # type: Dict[int, str]
        loadvalues(agree_dict, self.VAL_STRONGLY_AGREE,
                   self.VAL_STRONGLY_DISAGREE, "agreement_a")

        q_a_list = []  # type: List[str]

        def addqa(_fieldname: str, _valuedict: Dict[int, str]) -> None:
            xstringname = _fieldname + "_q"
            q_a_list.append(
                tr_qa(self.xstring(req, xstringname),  # not wxstring
                      get_from_dict(_valuedict, getattr(self, _fieldname)))
            )

        def subheading(_xstringname: str) -> None:
            q_a_list.append(subheading_spanning_two_columns(
                self.wxstring(req, _xstringname)))

        # Preamble
        addqa(self.FN_QA_RESPONDENT, respondent_dict)
        addqa(self.FN_QB_SERVICE_TYPE, service_dict)
        # The bulk
        subheading("q1_stem")
        for fieldname in self.Q1_FIELDS:
            addqa(fieldname, mh_dict)
        subheading("q2_stem")
        for fieldname in self.Q2_FIELDS:
            addqa(fieldname, agree_dict)
        if self.was_inpatient():
            subheading("q3_stem")
            for fieldname in self.Q3_FIELDS:
                addqa(fieldname, agree_dict)
        # General
        q_a_list.append(subheading_spanning_two_columns(
            req.wappstring("general")))
        q_a_list.append(tr_qa(
            self.wxstring(req, "general_comments_q"),
            self.general_comments
        ))
        q_a_list.append(tr_qa(
            self.wxstring(req, "participation_q"),
            get_yes_no_none(req, self.future_participation)
        ))
        if self.offering_participation():
            q_a_list.append(tr_qa(
                self.wxstring(req, "contact_details_q"),
                self.contact_details
            ))

        h = """
            <div class="{CssClass.SUMMARY}">
                <table class="{CssClass.SUMMARY}">
                    {tr_is_complete}
                </table>
            </div>
            <table class="{CssClass.TASKDETAIL}">
                <tr>
                    <th width="60%">Question</th>
                    <th width="40%">Answer</th>
                </tr>
                {q_a}
            </table>
            <div class="{CssClass.FOOTNOTES}">
            </div>
        """.format(
            CssClass=CssClass,
            tr_is_complete=self.get_is_complete_tr(req),
            q_a="\n".join(q_a_list),
        )
        return h

    # No SNOMED codes for Perinatal-POEM.