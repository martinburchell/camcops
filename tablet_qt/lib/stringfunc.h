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
#include <QStringList>


namespace stringfunc {

// ============================================================================
// Make sequences of strings
// ============================================================================

QStringList strseq(const QString& prefix, int first, int last);
// Example: stringSequence("q", 1, 3) -> {"q1", "q2", "q3"}

QStringList strseq(const QString& prefix, int first, int last,
                   const QString& suffix);
QStringList strseq(const QString& prefix, int first, int last,
                   const QStringList& suffixes);

QStringList strseq(const QStringList& prefixes, int first, int last);
QStringList strseq(const QStringList& prefixes, int first, int last,
                   const QStringList& suffixes);

// ============================================================================
// Other string formatting
// ============================================================================

QString strnum(const QString& prefix, int num);

// ============================================================================
// HTML processing
// ============================================================================

QString bold(const QString& str);
QString bold(int x);
QString joinHtmlLines(const QStringList& lines);
QString& toHtmlLinebreaks(QString& str,
                          bool convert_embedded_literals = true);

// ============================================================================
// Other string processing
// ============================================================================

QString& replaceFirst(QString& str, const QString& from, const QString& to);

}  // namespace stringfunc