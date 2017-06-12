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

#include "iesr.h"
#include "maths/mathfunc.h"
#include "lib/stringfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcqgrid.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"
using mathfunc::noneNull;
using mathfunc::sumInt;
using mathfunc::scorePhrase;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strnumlist;
using stringfunc::strseq;
#define TR(stringname, text) const QString stringname(QObject::tr(text))

const QString Iesr::IESR_TABLENAME("iesr");

const int FIRST_Q = 1;
const int N_QUESTIONS = 22;
const int MAX_TOTAL = 88;
const int MAX_AVOIDANCE = 32;
const int MAX_INTRUSION = 28;
const int MAX_HYPERAROUSAL = 28;
const QString QPREFIX("q");
const QVector<int> AVOIDANCE_QUESTIONS{5, 7, 8, 11, 12, 13, 17, 22};
const QVector<int> INTRUSION_QUESTIONS{1, 2, 3, 6, 9, 16, 20};
const QVector<int> HYPERAROUSAL_QUESTIONS{4, 10, 14, 15, 18, 19, 21};
const QString FN_EVENT("event");

TR(PROMPT_EVENT, "Event:");
TR(A0, "Not at all");
TR(A1, "A little bit");
TR(A2, "Moderately");
TR(A3, "Quite a bit");
TR(A4, "Extremely");


void initializeIesr(TaskFactory& factory)
{
    static TaskRegistrar<Iesr> registered(factory);
}


Iesr::Iesr(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, IESR_TABLENAME, false, false, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);
    addField(FN_EVENT, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Iesr::shortname() const
{
    return "IES-R";
}


QString Iesr::longname() const
{
    return tr("Impact of Events Scale – Revised (¶+)");
}


QString Iesr::menusubtitle() const
{
    return tr("22-item self-report scale. Data collection tool ONLY unless "
              "host institution adds scale text.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Iesr::isComplete() const
{
    return noneNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


QStringList Iesr::summary() const
{
    return QStringList{
        totalScorePhrase(totalScore(), MAX_TOTAL),
        scorePhrase("Avoidance", avoidanceScore(), MAX_AVOIDANCE),
        scorePhrase("Intrusion", intrusionScore(), MAX_INTRUSION),
        scorePhrase("Hyperarousal", hyperarousalScore(), MAX_HYPERAROUSAL),
    };
}


QStringList Iesr::detail() const
{
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "", ": ", QPREFIX, FIRST_Q, N_QUESTIONS);
    lines.append("");
    lines += summary();
    return lines;
}


OpenableWidget* Iesr::editor(bool read_only)
{
    NameValueOptions options{
        {A0, 0},
        {A1, 1},
        {A2, 2},
        {A3, 3},
        {A4, 4},
    };

    QVector<QuestionWithOneField> qfields;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        QString qstr = strnum(QPREFIX, i);
        qfields.append(QuestionWithOneField(xstring(qstr), fieldRef(qstr)));
    }

    QuPagePtr page = QuPagePtr((new QuPage{
        (new QuText(xstring("instruction_1")))->setBold(),
        new QuText(PROMPT_EVENT),
        new QuTextEdit(fieldRef(FN_EVENT)),
        (new QuText(xstring("instruction_2")))->setBold(),
        new QuMcqGrid(qfields, options),
    })->setTitle(longname()));

    Questionnaire* questionnaire = new Questionnaire(m_app, {page});
    questionnaire->setType(QuPage::PageType::Patient);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Iesr::totalScore() const
{
    return sumInt(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)));
}


int Iesr::avoidanceScore() const
{
    return sumInt(values(strnumlist(QPREFIX, AVOIDANCE_QUESTIONS)));
}


int Iesr::intrusionScore() const
{
    return sumInt(values(strnumlist(QPREFIX, INTRUSION_QUESTIONS)));
}


int Iesr::hyperarousalScore() const
{
    return sumInt(values(strnumlist(QPREFIX, HYPERAROUSAL_QUESTIONS)));
}
