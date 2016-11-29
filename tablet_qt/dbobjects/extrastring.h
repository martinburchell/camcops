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

#pragma once
#include "db/databaseobject.h"


class ExtraString : public DatabaseObject
{
public:
    // Specimen constructor:
    ExtraString(const QSqlDatabase& db);
    // String loading constructor:
    ExtraString(const QSqlDatabase& db,
                const QString& task,
                const QString& name);
    // String saving constructor:
    ExtraString(const QSqlDatabase& db,
                const QString& task,
                const QString& name,
                const QString& value);
    virtual ~ExtraString();
    QString value() const;
    bool exists() const;
    bool anyExist(const QString& task) const;  // sort-of static function
    void deleteAllExtraStrings();  // sort-of static function
protected:
    void commonConstructor();
    bool m_exists;
};
