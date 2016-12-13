/*
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

#include "dbconstants.h"
#include <QDebug>


namespace DbConst {

    const QString PK_FIELDNAME("id");
    const QString MODIFICATION_TIMESTAMP_FIELDNAME("when_last_modified");
    const QString MOVE_OFF_TABLET_FIELDNAME("_move_off_tablet");
    // ... must match database.py on server

    const QString CREATION_TIMESTAMP_FIELDNAME("when_created");
    const int NONEXISTENT_PK = -1;

    const int NUMBER_OF_IDNUMS = 8;
    const QString BAD_IDNUM_DESC("<bad_idnum>");
    const QString UNKNOWN_IDNUM_DESC("<ID_number_%1>");
    const QString IDDESC_FIELD_FORMAT("iddesc%1");
    const QString IDSHORTDESC_FIELD_FORMAT("idshortdesc%1");
}


bool DbConst::isValidWhichIdnum(int which_idnum)
{
    bool valid = which_idnum >= 1 && which_idnum <= NUMBER_OF_IDNUMS;
    if (!valid) {
        qWarning() << Q_FUNC_INFO << "bad idnum" << which_idnum;
    }
    return valid;
}
