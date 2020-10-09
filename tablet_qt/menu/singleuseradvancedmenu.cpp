/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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

#include "lib/uifunc.h"
#include "menulib/serversettingswindow.h"
#include "singleuseradvancedmenu.h"

SingleUserAdvancedMenu::SingleUserAdvancedMenu(CamcopsApp& app) :
    MenuWindow(app, uifunc::iconFilename(uiconst::ICON_SETTINGS))
{
}


QString SingleUserAdvancedMenu::title() const
{
    return tr("Advanced options");
}


void SingleUserAdvancedMenu::makeItems()
{
    m_items = {
        MenuItem(tr("Advanced settings")).setLabelOnly(),
        MenuItem(
            tr("Configure server settings"),
            MenuItem::OpenableWidgetMaker(
                std::bind(&SingleUserAdvancedMenu::configureServer, this,
                          std::placeholders::_1)
            )
        )
    };
}

OpenableWidget* SingleUserAdvancedMenu::configureServer(CamcopsApp& app)
{
    auto window = new ServerSettingsWindow(app);

    return window->editor();
}
