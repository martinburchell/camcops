#include "storedvar.h"
#include "lib/uifunc.h"

const QString STOREDVAR_TABLENAME = "storedvar";

const QString NAME_FIELDNAME = "name";
const QString TYPE_FIELDNAME = "type";
// - No need to keep to legacy fieldnames (valueInteger, valueReal, valueText)
//   as we'll no longer be uploading these.
const QString VALUE_BOOL_FIELDNAME = "value_bool";
const QString VALUE_INTEGER_FIELDNAME = "value_integer";
const QString VALUE_REAL_FIELDNAME = "value_real";
const QString VALUE_TEXT_FIELDNAME = "value_text";

// - Also, SQLite is typeless... could make use of that, and store all values
//   in the same column. But for generality:
const QMap<QVariant::Type, QString> COLMAP{
    // Which database field shall we use to store each QVariant type?
    {QVariant::Bool, VALUE_BOOL_FIELDNAME},
    {QVariant::Int, VALUE_INTEGER_FIELDNAME},
    {QVariant::Double, VALUE_REAL_FIELDNAME},
    {QVariant::String, VALUE_TEXT_FIELDNAME},
};
const QMap<QVariant::Type, QString> TYPEMAP{
    // What value should we put in the 'type' database column to indicate
    // the QVariant type in use?
    // http://doc.qt.io/qt-5/qvariant-obsolete.html#Type-enum
    {QVariant::Bool, "Bool"},
    {QVariant::Int, "Int"},
    {QVariant::Double, "Double"},
    {QVariant::String, "String"},
};


StoredVar::StoredVar(const QSqlDatabase& db, const QString& name,
                     QVariant::Type type, QVariant default_value) :
    DatabaseObject(db, STOREDVAR_TABLENAME),
    m_name(name),
    m_type(type),
    m_value_fieldname("")
{
    // ------------------------------------------------------------------------
    // Define fields
    // ------------------------------------------------------------------------
    addField(NAME_FIELDNAME, QVariant::String, true, true, false);
    addField(TYPE_FIELDNAME, QVariant::String, true, false, false);
    QMapIterator<QVariant::Type, QString> i(COLMAP);
    while (i.hasNext()) {
        i.next();
        QVariant::Type fieldtype = i.key();
        QString fieldname = i.value();
        if (!hasField(fieldname)) {
            // We can have duplicate/overlapping fieldnames, and it will be
            // happy (if the types are appropriately interconvertible).
            // The Field will have the type of the FIRST one inserted.
            // However, it is dreadfully confusing if you put the Bool
            // definition before the Int one, and all your integers are
            // converted to 1 or 0. So use different ones!
            addField(fieldname, fieldtype, false, false, false);
        }
        if (fieldtype == type) {
            // Define our primary field
            m_value_fieldname = fieldname;
        }
    }
    if (m_value_fieldname.isEmpty()) {
        UiFunc::stopApp(QString(
            "StoredVar::StoredVar: m_value_fieldname unknown to StoredVar "
            "with name=%1, type=%2; is the type missing from COLMAP?")
                        .arg(name, type));
    }
    if (!TYPEMAP.contains(type)) {
        qCritical() << Q_FUNC_INFO << "QVariant type unknown:" << type;
        UiFunc::stopApp(
            "StoredVar::StoredVar: type unknown to StoredVar; see debug "
            "console for details and check TYPEMAP");
    }

    // ------------------------------------------------------------------------
    // Load from database (or create/save), unless this is a specimen
    // ------------------------------------------------------------------------
    if (!name.isEmpty()) {
        // Not a specimen; load, or set defaults and save
        bool success = load(NAME_FIELDNAME, name);
        if (!success) {
            setValue(NAME_FIELDNAME, name);
            setValue(TYPE_FIELDNAME, TYPEMAP[type]);
            // qDebug() << "Setting type to:" << type;
            setValue(default_value);
            save();
        }
    }
}


StoredVar::~StoredVar()
{
}


bool StoredVar::setValue(const QVariant &value, bool save_to_db)
{
    qDebug() << Q_FUNC_INFO << value;
    bool changed = setValue(m_value_fieldname, value);
    if (save_to_db) {
        save();
    }
    return changed;
}


QVariant StoredVar::value() const
{
    QVariant v = value(m_value_fieldname);
    v.convert(m_type);
    return v;
}


QString StoredVar::name() const
{
    return m_name;
}
