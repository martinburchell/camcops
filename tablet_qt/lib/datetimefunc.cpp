#include "datetimefunc.h"
#include <QTimeZone>
#include <QVariant>

const QString DateTime::SHORT_DATETIME_FORMAT("yyyy-MM-dd HH:mm");  // 2000-12-31 23:59
const QString DateTime::SHORT_DATE_FORMAT("yyyy-MM-dd");  // 2000-12-31
const QString DateTime::TEXT_DATE_FORMAT("dd MMM yyyy");  // 31 Dec 2000
const QString DateTime::UNKNOWN("?");


// http://stackoverflow.com/questions/21976264/qt-isodate-formatted-date-time-including-timezone

QString DateTime::datetimeToIsoMs(const QDateTime& dt)
{
    // An ISO-8601 format preserving millisecond accuracy and timezone.
    // Equivalent in moment.js: thing.format("YYYY-MM-DDTHH:mm:ss.SSSZ")
    // Example: '2016-06-02T10:04:03.588+01:00'
    // Here we also allow 'Z' for UTC.

    // In Qt, BEWARE:
    //      dt;  // QDateTime(2016-06-02 10:28:06.708 BST Qt::TimeSpec(LocalTime))
    //      dt.toString(Qt::ISODate);  // "2016-06-02T10:28:06" -- DROPS timezone
    if (!dt.isValid()) {
        return "";
    }
    QString localtime = dt.toString("yyyy-MM-ddTHH:mm:ss.zzz");
    int offset_from_utc_s = dt.offsetFromUtc();
    // FOR TESTING: offsetFromUtcSec = -(3600 * 2.5);
    QString tzinfo;
    if (offset_from_utc_s == 0) {
        tzinfo = "Z";
    } else {
        QString sign = offset_from_utc_s < 0 ? "-" : "+";
        offset_from_utc_s = abs(offset_from_utc_s);
        int hours = offset_from_utc_s / 3600;
        int minutes = (offset_from_utc_s % 3600) / 60;
        tzinfo += QString("%1%2:%3").arg(sign)
            .arg(hours, 2, 10, QChar('0'))
            .arg(minutes, 2, 10, QChar('0'));
        // http://stackoverflow.com/questions/2618414/convert-an-int-to-a-qstring-with-zero-padding-leading-zeroes
    }
    return localtime + tzinfo;
}


QString DateTime::datetimeToIsoMsUtc(const QDateTime& dt)
{
    QDateTime utc_dt = dt.toTimeSpec(Qt::UTC);
    return datetimeToIsoMs(utc_dt);
}


QDateTime DateTime::isoToDateTime(const QString& iso)
{
    return QDateTime::fromString(iso, Qt::ISODate);
}


QDateTime DateTime::now()
{
    return QDateTime::currentDateTime();
}


QDate DateTime::nowDate()
{
    return QDate::currentDate();
}


QString DateTime::shortDateTime(const QDateTime& dt)
{
    return dt.toString(SHORT_DATETIME_FORMAT);
}


QString DateTime::shortDate(const QDate& d)
{
    return d.toString(SHORT_DATE_FORMAT);
}


QString DateTime::textDate(const QDate& d)
{
    return d.toString(TEXT_DATE_FORMAT);
}


QString DateTime::textDate(const QVariant& date)
{
    if (date.isNull()) {
        return UNKNOWN;
    }
    return textDate(date.toDate());
}


int DateTime::ageYearsFrom(const QDate& from, const QDate& to)
{
    // Unhelpful:
    // https://forum.qt.io/topic/27906/difference-in-days-months-and-years-between-two-dates/9
    if (from > to) {
        return -ageYearsFrom(to, from);
    }
    // Now, "birthday age" calculation.
    // Examples:                                yeardiff    delta
    // * 1 Jan 2000 ->  1 Jan 2000 = age 0      0           0
    // * 1 Jan 2000 -> 31 Dec 2000 = age 0      0           0
    // * 1 Jun 2000 -> 31 Apr 2001 = age 0      1           -1
    // * 2 Jun 2000 ->  1 Jun 2001 = age 0      1           -1
    // * 2 Jun 2000 ->  2 Jun 2001 = age 1      1           0
    int years = to.year() - from.year();
    if (to.month() < from.month() ||
            (to.month() == from.month() && to.day() < from.day())) {
        years -= 1;
    }
    return years;
}


int DateTime::ageYears(const QVariant& dob, int default_years)
{
    if (dob.isNull()) {
        return default_years;
    }
    return ageYearsFrom(dob.toDate(), nowDate());
}
