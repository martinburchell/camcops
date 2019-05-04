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

#include "clinicalsetsmenu.h"
#include "common/uiconst.h"
#include "lib/uifunc.h"
#include "menulib/menuitem.h"

#include "menu/setmenucpftaffective1.h"
#include "menu/setmenucpftperinatal1.h"
#include "menu/setmenucpftpsychooncology1.h"
#include "menu/setmenufromlp.h"
#include "menu/setmenufromperinatal.h"
#include "menu/setmenuobrien1.h"


ClinicalSetsMenu::ClinicalSetsMenu(CamcopsApp& app) :
    MenuWindow(app,
               uifunc::iconFilename(uiconst::ICON_SETS_CLINICAL))
{
}


QString ClinicalSetsMenu::title() const
{
    return tr("Sets of tasks collected together for clinical purposes");
}


void ClinicalSetsMenu::makeItems()
{
    m_items = {
        MAKE_CHANGE_PATIENT(m_app),
        MAKE_MENU_MENU_ITEM(SetMenuCpftAffective1, m_app),
        MAKE_MENU_MENU_ITEM(SetMenuCpftPerinatal1, m_app),
        MAKE_MENU_MENU_ITEM(SetMenuCpftPsychooncology1, m_app),
        MAKE_MENU_MENU_ITEM(SetMenuFromLp, m_app),
        MAKE_MENU_MENU_ITEM(SetMenuFromPerinatal, m_app),
        MAKE_MENU_MENU_ITEM(SetMenuOBrien1, m_app),
    };
}
