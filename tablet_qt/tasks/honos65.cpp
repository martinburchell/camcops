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

#include "honos65.h"
#include "lib/mathfunc.h"
#include "lib/stringfunc.h"
#include "questionnairelib/namevaluepair.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qulineedit.h"
#include "tasklib/taskfactory.h"
using mathfunc::anyNull;
using mathfunc::noneNull;
using mathfunc::scoreString;
using mathfunc::sumInt;
using mathfunc::totalScorePhrase;
using stringfunc::strnum;
using stringfunc::strseq;

const int FIRST_Q = 1;
const int N_QUESTIONS = 12;
const int MAX_SCORE = 48;
const QString QPREFIX("q");

const QString HONOS65_TABLENAME("honos65");

const QString PERIOD_RATED("period_rated");
const QString Q8("q8");
const QString Q8_PROBLEM_TYPE("q8problemtype");
const QString Q8_OTHER_PROBLEM("q8otherproblem");
const QString VALUE_OTHER("J");

// #define PREVENT_Q8_PROBLEM_UNLESS_RATED  // just looks odd...


void initializeHonos65(TaskFactory& factory)
{
    static TaskRegistrar<Honos65> registered(factory);
}


Honos65::Honos65(CamcopsApp& app, const QSqlDatabase& db, int load_pk) :
    Task(app, db, HONOS65_TABLENAME, false, true, false)  // ... anon, clin, resp
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);
    addField(PERIOD_RATED, QVariant::String);
    addField(Q8_PROBLEM_TYPE, QVariant::String);
    addField(Q8_OTHER_PROBLEM, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}


// ============================================================================
// Class info
// ============================================================================

QString Honos65::shortname() const
{
    return "HoNOS 65+";
}


QString Honos65::longname() const
{
    return tr("Health of the Nation Outcome Scales, older adults");
}


QString Honos65::menusubtitle() const
{
    return tr("12-item clinician-rated scale.");
}


QString Honos65::infoFilenameStem() const
{
    return "honos";
}


// ============================================================================
// Instance info
// ============================================================================

bool Honos65::isComplete() const
{
    if (anyNull(values(strseq(QPREFIX, FIRST_Q, N_QUESTIONS)))) {
        return false;
    }
    int q8 = valueInt(Q8);
    if (q8 != 0 && q8 != 9 && valueIsNullOrEmpty(Q8_PROBLEM_TYPE)) {
        return false;
    }
    if (q8 != 0 && q8 != 9 && valueString(Q8_PROBLEM_TYPE) == VALUE_OTHER &&
            valueIsNullOrEmpty(Q8_OTHER_PROBLEM)) {
        return false;
    }
    return !valueIsNullOrEmpty(PERIOD_RATED);
}


QStringList Honos65::summary() const
{
    return QStringList{totalScorePhrase(totalScore(), MAX_SCORE)};
}


QStringList Honos65::detail() const
{
    QStringList lines = completenessInfo();
    lines += fieldSummaries("q", "_s", " ", QPREFIX, FIRST_Q, 8);
    lines += fieldSummary(Q8_PROBLEM_TYPE, xstring("q8problemtype_s"));
    lines += fieldSummary(Q8_OTHER_PROBLEM, xstring("q8otherproblem_s"));
    lines += fieldSummaries("q", "_s", " ", QPREFIX, 9, N_QUESTIONS);
    lines.append("");
    lines += summary();
    return lines;
}


OpenableWidget* Honos65::editor(bool read_only)
{
    NameValueOptions q8_problemtype_options{
        {xstring("q8problemtype_option_a"), "A"},
        {xstring("q8problemtype_option_b"), "B"},
        {xstring("q8problemtype_option_c"), "C"},
        {xstring("q8problemtype_option_d"), "D"},
        {xstring("q8problemtype_option_e"), "E"},
        {xstring("q8problemtype_option_f"), "F"},
        {xstring("q8problemtype_option_g"), "G"},
        {xstring("q8problemtype_option_h"), "H"},
        {xstring("q8problemtype_option_i"), "I"},
        {xstring("q8problemtype_option_j"), "J"},
    };
    QVector<QuPagePtr> pages;

    auto getoptions = [this](int n) -> NameValueOptions {
        NameValueOptions options;
        for (int i = 0; i <= 4; ++i) {
            QString name = xstring(QString("q%1_option%2").arg(n).arg(i));
            options.append(NameValuePair(name, i));
        }
        options.append(NameValuePair(xstring("option9"), 9));
        return options;
    };

    auto addpage = [this, &pages, &getoptions,
                    &q8_problemtype_options](int n) -> void {
        NameValueOptions options = getoptions(n);
        QString pagetitle = xstring("title_prefix") + QString::number(n);
        QString question = xstring(strnum("q", n));
        QString fieldname = strnum(QPREFIX, n);
        QVector<QuElement*> elements{
            new QuText(question),
            new QuMcq(fieldRef(fieldname), options),
        };
        if (n == 8) {
            elements += QVector<QuElement*>{
                new QuText(xstring("q8problemtype_prompt")),
                new QuMcq(fieldRef(Q8_PROBLEM_TYPE), q8_problemtype_options),
                new QuText(xstring("q8otherproblem_prompt")),
                new QuLineEdit(fieldRef(Q8_OTHER_PROBLEM)),
            };
        }
        pages.append(QuPagePtr((new QuPage(elements))->setTitle(pagetitle)));
    };

    pages.append(getClinicianDetailsPage());
    pages.append(QuPagePtr((new QuPage{
        new QuText(xstring("period_rated")),
        new QuLineEdit(fieldRef(PERIOD_RATED)),
        new QuText(xstring("instructions")),
    })->setTitle(xstring("firstpage_title"))));

    for (int n = FIRST_Q; n <= N_QUESTIONS; ++n) {
        addpage(n);
    }

    connect(fieldRef(Q8).data(), &FieldRef::valueChanged,
            this, &Honos65::updateMandatory);
    connect(fieldRef(Q8_PROBLEM_TYPE).data(), &FieldRef::valueChanged,
            this, &Honos65::updateMandatory);

    updateMandatory(nullptr, nullptr);

    Questionnaire* questionnaire = new Questionnaire(m_app, pages);
    questionnaire->setType(QuPage::PageType::Clinician);
    questionnaire->setReadOnly(read_only);
    return questionnaire;
}


// ============================================================================
// Task-specific calculations
// ============================================================================

int Honos65::totalScore() const
{
    int total = 0;
    for (int i = FIRST_Q; i <= N_QUESTIONS; ++i) {
        int v = valueInt(strnum(QPREFIX, i));
        if (v != 9) {  // 9 is "not known"
            total += v;
        }
    }
    return total;
}


// ============================================================================
// Signal handlers
// ============================================================================

void Honos65::updateMandatory(const FieldRef* fieldref,
                            const QObject* originator)
{
    // DANGER HERE: if we use setValue(), the signals can circle back to us, as
    // several fieldrefs have their valueChanged signal linked in here.
    // The only way to manage this, within this particular signalling
    // mechanism, is to make sure we mark ourselves as the originator on ALL
    // signals we trigger (via setValue() and setMandatory() calls), and to
    // reject any incoming calls for which we were the originator.
    //
    // Works fine now, but still looks a bit odd to the user - un#defined.

    Q_UNUSED(fieldref);
    if (originator == this) {
        return;  // or we will have an infinite loop crash
    }

    QVariant q8var = value(Q8);
    int q8int = q8var.toInt();

#ifdef PREVENT_Q8_PROBLEM_UNLESS_RATED
    bool must_not_have_q8_problem_type = !q8var.isNull() && (q8int == 0 ||
                                                             q8int == 9);
    if (must_not_have_q8_problem_type) {
        // Force the problem type to be blank.
        // WATCH OUT: potential for infinite loop if we let it signal back
        // (indirectly, to here): see check on originator, above.
        fieldRef(Q8_PROBLEM_TYPE)->setValue(QVariant(), this);
    }
#endif

    bool need_q8_problem_type = !q8var.isNull() && q8int != 0 && q8int != 9;
    fieldRef(Q8_PROBLEM_TYPE)->setMandatory(need_q8_problem_type, this);
    fieldRef(Q8_OTHER_PROBLEM)->setMandatory(
                valueString(Q8_PROBLEM_TYPE) == VALUE_OTHER, this);
}
