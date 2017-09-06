#!/usr/bin/env python
# camcops_server/tasks/progressnote.py

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

import cardinal_pythonlib.rnc_web as ws
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import UnicodeText

from ..cc_modules.cc_ctvinfo import CtvInfo
from ..cc_modules.cc_html import answer
from ..cc_modules.cc_request import CamcopsRequest
from ..cc_modules.cc_sqlalchemy import Base
from ..cc_modules.cc_task import (
    Task,
    TaskHasClinicianMixin,
    TaskHasPatientMixin,
)


# =============================================================================
# ProgressNote
# =============================================================================

class ProgressNote(TaskHasPatientMixin, TaskHasClinicianMixin, Task):
    __tablename__ = "progressnote"
    shortname = "ProgressNote"
    longname = "Clinical progress note"

    location = Column("location", UnicodeText, comment="Location")
    note = Column("note", UnicodeText, comment="Clinical note")

    def get_clinical_text(self, req: CamcopsRequest) -> List[CtvInfo]:
        return [CtvInfo(content=ws.webify(self.note))]

    def is_complete(self) -> bool:
        return self.note is not None

    def get_task_html(self, req: CamcopsRequest) -> str:
        # Avoid tables - PDF generator crashes if text is too long.
        h = """
            <div class="heading">
                {heading_location}
            </div>
            <div>
                {location}
            </div>
            <div class="heading">
                {heading_note}
            </div>
            <div>
                {note}
            </div>
        """.format(
            heading_location=req.wappstring("location"),
            location=answer(ws.webify(self.location),
                            default_for_blank_strings=True),
            heading_note=req.wappstring("note"),
            note=answer(self.note, default_for_blank_strings=True),
        )
        return h
