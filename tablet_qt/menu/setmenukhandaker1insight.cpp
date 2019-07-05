/*
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
*/

#include "setmenukhandaker1insight.h"
#include "common/textconst.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "tasks/bdi.h"
#include "tasks/cisr.h"
#include "tasks/khandaker1insightmedical.h"


SetMenuKhandaker1Insight::SetMenuKhandaker1Insight(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETS_RESEARCH))
{
}


QString SetMenuKhandaker1Insight::title() const
{
    return tr("Khandaker GM — 1 — Insight study");
}


QString SetMenuKhandaker1Insight::subtitle() const
{
    return tr("Khandaker GM, University of Cambridge, UK — "
              "Insight immunopsychiatry study");
}


void SetMenuKhandaker1Insight::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_TASK_MENU_ITEM(Bdi::BDI_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(Cisr::CISR_TABLENAME, m_app),
        MAKE_TASK_MENU_ITEM(
            Khandaker1InsightMedical::KHANDAKER1INSIGHTMEDICAL_TABLENAME, m_app),
    };
}