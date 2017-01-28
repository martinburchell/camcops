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

#include "field.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "lib/datetimefunc.h"


Field::Field(const QString& name, QVariant::Type type,
             bool mandatory, bool unique, bool pk) :
    m_name(name),
    m_type(type),
    m_pk(pk),
    m_unique(unique),
    m_mandatory(mandatory),
    m_set(false),
    m_dirty(true)
{
    if (pk) {
        m_unique = true;
        m_mandatory = true;
    }
//    if (type == QVariant::String || type == QVariant::Char) {
//        m_default_value = "";  // empty string, not NULL (as per Django)
//    } else {
//        m_default_value = QVariant(type);  // NULL
//    }
    m_default_value = QVariant(type);  // NULL
    m_value = m_default_value;
}


Field::Field() :  // needed by QMap
    Field("", QVariant::Int)
{
    // delegating constructor (C++11)
}


Field& Field::setPk(bool pk)
{
    m_pk = pk;
    return *this;
}


Field& Field::setUnique(bool unique)
{
    m_unique = unique;
    return *this;
}


Field& Field::setMandatory(bool mandatory)
{
    m_mandatory = mandatory;
    return *this;
}


Field& Field::setDefaultValue(QVariant value)
{
    m_default_value = value;
    m_default_value.convert(m_type);
    if (!m_set) {
        m_value = m_default_value;
    }
    return *this;
}


QString Field::name() const
{
    return m_name;
}


QVariant::Type Field::type() const
{
    return m_type;
}


bool Field::isPk() const
{
    return m_pk;
}


bool Field::isUnique() const
{
    return m_unique;
}


bool Field::isMandatory() const
{
    return m_mandatory;
}


bool Field::allowsNull() const
{
    // SQLite allows NULL values in primary keys, but this is a legacy of
    // bugs in early SQLite versions.
    // http://www.sqlite.org/lang_createtable.html
    return m_mandatory || m_pk;
}


QString Field::sqlColumnDef() const
{
    QString type = sqlColumnType();
    if (m_pk) {
        type += " PRIMARY KEY";
    }
    // AUTOINCREMENT usually not required: https://www.sqlite.org/autoinc.html
    if (m_unique && !m_pk) {
        type += " UNIQUE";
    }
    if (allowsNull()) {
        type += " NOT NULL";
    }
    return type;
}


QVariant Field::value() const
{
    return m_value;
}


QString Field::prettyValue() const
{
    return convert::prettyValue(m_value, m_type);
}


bool Field::setValue(const QVariant& value)
{
    if (!m_set || value != m_value) {
        m_dirty = true;
    }
    m_value = value;
    m_value.convert(m_type);
    m_set = true;
    return m_dirty;
}


bool Field::nullify()
{
    if (!m_set || !isNull()) {
        m_dirty = true;
    }
    m_value = QVariant(m_type);
    m_set = true;
    return m_dirty;
}


bool Field::isNull() const
{
    return m_value.isNull();
}


bool Field::isDirty() const
{
    return m_dirty;
}


void Field::setDirty()
{
    m_dirty = true;
}


void Field::clearDirty()
{
    m_dirty = false;
}


QDebug operator<<(QDebug debug, const Field& f)
{
    if (f.m_value.isNull()) {
        debug.nospace() << "NULL (" << QVariant::typeToName(f.m_type) << ")";
    } else {
        debug.nospace() << f.m_value;
    }
    if (f.m_dirty) {
        debug.nospace() << " (*)";
    }
    return debug;
}


QString Field::sqlColumnType() const
{
    // SQLite types: https://www.sqlite.org/datatype3.html
    //      SQLite uses up to 8 bytes (depending on actual value) and
    //      integers are signed, so the maximum INTEGER
    //      is 2^63 - 1 = 9,223,372,036,854,775,807
    // C++ types:
    //      int -- typically 32-bit; not guaranteed on all C++ platforms,
    //             though 32-bit on all Qt platforms, I think
    // Qt types: http://doc.qt.io/qt-5/qtglobal.html
    //      - qint8, qint16, qint32, qint64...
    //      - standard int is int32
    //        32-bit signed: up to
    //      - qlonglong is the same as qint64
    //        64-bit signed: up to +9,223,372,036,854,775,807 = 9223372036854775807
    //      - qulonglong
    //        64-bit unsigned: 0 to +18,446,744,073,709,551,615 = 18446744073709551615
    // C++ type name: QVariant::typeToName(m_type);
    switch (m_type) {
    case QVariant::Int:  // normally 32-bit
    case QVariant::UInt:  // normally 32-bit
    case QVariant::Bool:
    case QVariant::LongLong:  // 64-bit
    case QVariant::ULongLong:  // 64-bit
        return "INTEGER";
    case QVariant::Double:
        return "REAL";
    case QVariant::String:
    case QVariant::Char:
    case QVariant::Date:
    case QVariant::Time:
    case QVariant::DateTime:
    case QVariant::Uuid:
        return "TEXT";
    case QVariant::ByteArray:
        return "BLOB";
    default:
        uifunc::stopApp("Field::sqlColumnType: Unknown field type: " +
                        m_type);
    }
    return "";
}


void Field::setFromDatabaseValue(const QVariant& db_value)
{
    // SQLite -> C++
    switch (m_type) {
    case QVariant::DateTime:
        m_value = QVariant(datetime::isoToDateTime(db_value.toString()));
        break;
    case QVariant::Char:
        // If you just do "m_value = db_value", it will become an invalid
        // value when the convert() call is made below, so will appear as NULL.
        {
            QString str = db_value.toString();
            if (str.isEmpty()) {
                m_value.clear();
            } else {
                m_value = str.at(0);
            }
        }
        break;
    default:
        m_value = db_value;
        break;
    }
    m_value.convert(m_type);
    m_dirty = false;
}


QVariant Field::databaseValue() const
{
    // C++ -> SQLite
    if (m_value.isNull()) {
        return m_value;  // NULL
    }
    switch (m_type) {
    case QVariant::DateTime:
        return QVariant(datetime::datetimeToIsoMs(m_value.toDateTime()));
    case QVariant::Uuid:
        return m_value.toString();
        // see http://doc.qt.io/qt-5/quuid.html#toString; e.g.
        // "{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}" where 'x' is a hex digit
    default:
        return m_value;
    }
}