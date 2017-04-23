/*
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
*/

#pragma once
#include <QSqlDatabase>
#include <QSqlQuery>
#include "common/camcopsapp.h"
#include "db/dbfunc.h"
#include "db/sqlargs.h"


namespace ancillaryfunc
{

// ============================================================================
// Assistance function to load multiple ancillary objects
// - Class must inherit from DatabaseObject
// - Class must have a constructor like SomeAncillary(app, db, pk)
// ============================================================================

template<class AncillaryType, class AncillaryPtrType>
void loadAncillary(QVector<AncillaryPtrType>& ancillaries,
                   CamcopsApp& app,
                   const QSqlDatabase& db,
                   const QString& fk_name,
                   const OrderBy& order_by,
                   int parent_pk)
{
    ancillaries.clear();
    WhereConditions where;
    where[fk_name] = parent_pk;
    AncillaryType specimen(app, db);
    SqlArgs sqlargs = specimen.fetchQuerySql(where, order_by);
    QSqlQuery query(db);
    bool success = dbfunc::execQuery(query, sqlargs);
    if (success) {  // success check may be redundant (cf. while clause)
        while (query.next()) {
            AncillaryPtrType ancillary(new AncillaryType(
                                       app, db, dbconst::NONEXISTENT_PK));
            ancillary->setFromQuery(query, true);
            ancillaries.append(ancillary);
        }
    }
}


}  // namespace ancillaryfunc