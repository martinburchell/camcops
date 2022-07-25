/*
    Copyright (C) 2012, University of Cambridge, Department of Psychiatry.
    Created by Rudolf Cardinal (rnc1001@cam.ac.uk).

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
    along with CamCOPS. If not, see <https://www.gnu.org/licenses/>.
*/

#include "paradise24.h"
#include "common/textconst.h"
#include "lib/stringfunc.h"
#include "maths/mathfunc.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/questionnairefunc.h"
#include "questionnairelib/qugridcontainer.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/quheight.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumass.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/quunitselector.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using mathfunc::meanOrNull;
using stringfunc::strnumlist;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int LAST_Q = 24;
const int MIN_SCORE = 0;
const int MAX_SCORE = 2;
const QString Q_PREFIX("q");

const QString Paradise24::PARADISE24_TABLENAME("paradise24");


void initializeParadise24(TaskFactory& factory)
{
    static TaskRegistrar<Paradise24> registered(factory);
}

Paradise24::Paradise24(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, PARADISE24_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(Q_PREFIX, FIRST_Q, LAST_Q), QVariant::Int);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Paradise24::shortname() const
{
    return "PARADISE-24";
}


QString Paradise24::longname() const
{
    return tr("PARADISE-24");
}


QString Paradise24::description() const
{
    return tr("A Measure to Assess the Impact of Brain Disorders on People’s Lives");
}


QStringList Paradise24::fieldNames() const
{
    auto field_names = strseq(Q_PREFIX, FIRST_Q, LAST_Q);

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Paradise24::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList Paradise24::summary() const
{
    return QStringList{};
}


QStringList Paradise24::detail() const
{
    QStringList lines = completenessInfo();

    const QString spacer = " ";
    const QString suffix = "";

    const QStringList fieldnames = fieldNames();

    for (int i = 0; i < fieldnames.length(); ++i) {
        const QString& fieldname = fieldnames.at(i);
        lines.append(fieldSummary(fieldname, xstring(fieldname),
                                  spacer, suffix));
    }


    lines.append("");
    lines += summary();

    return lines;
}


OpenableWidget* Paradise24::editor(const bool read_only)
{
    NameValueOptions options;

    for (int i = MIN_SCORE; i <= MAX_SCORE; ++i) {
        auto name = QString("option_%1").arg(i);

        options.append({xstring(name), i});
    }

    const int min_width_px = 100;
    const QVector<int> min_option_widths_px = {50, 50, 50};

    auto instructions = new QuHeading(xstring("instructions"));
    auto grid = buildGrid(FIRST_Q, LAST_Q, options);
    grid->setMinimumWidthInPixels(min_width_px,
                                  min_option_widths_px);

    QVector<QuElement*> elements{
        instructions,
        grid,
    };

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title")));

    auto questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);

    return questionnaire;
}


QuMcqGrid* Paradise24::buildGrid(int first_qnum,
                                 int last_qnum,
                                 const NameValueOptions options)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = Q_PREFIX + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));
    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    // Repeat options every six lines
    QVector<McqGridSubtitle> subtitles{
        {6, ""},
        {12, ""},
        {18, ""},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
