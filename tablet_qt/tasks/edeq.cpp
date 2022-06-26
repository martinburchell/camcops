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

#include "edeq.h"
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
const int N_QUESTIONS = 28;
const int MIN_SCORE = 0;
const int MAX_SCORE = 7;
const int MIN_SUBSCALE = 0;
const int MAX_SUBSCALE = 7;
const QString QPREFIX("q");
const QVector<int> RESTRAINT_QUESTIONS{1, 2, 3, 4, 5};
const QVector<int> EATING_CONCERN_QUESTIONS{7, 9, 19, 20, 21};
const QVector<int> SHAPE_CONCERN_QUESTIONS{6, 8, 10, 11, 23, 26, 27, 28};
const QVector<int> WEIGHT_CONCERN_QUESTIONS{8, 12, 22, 24, 25};

const QString Q_MASS_KG("q_mass_kg");
const QString Q_HEIGHT_M("q_height_m");
const QString Q_NUM_PERIODS_MISSED("q_num_periods_missed");
const QString Q_PILL("q_pill");

const QString Edeq::EDEQ_TABLENAME("edeq");


void initializeEdeq(TaskFactory& factory)
{
    static TaskRegistrar<Edeq> registered(factory);
}

Edeq::Edeq(CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, EDEQ_TABLENAME, false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr),
    m_have_missed_periods_fr(nullptr),
    m_num_periods_missed_grid(nullptr)
{
    addFields(strseq(QPREFIX, FIRST_Q, N_QUESTIONS), QVariant::Int);

    addField(Q_MASS_KG, QVariant::Double);
    addField(Q_HEIGHT_M, QVariant::Double);
    addField(Q_NUM_PERIODS_MISSED, QVariant::Int, false, false, false, 0);
    addField(Q_PILL, QVariant::Bool, false, false, false, false);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}
// ============================================================================
// Class info
// ============================================================================

QString Edeq::shortname() const
{
    return "EDE-Q";
}


QString Edeq::longname() const
{
    return tr("Eating Disorder Examination Questionnaire");
}


QString Edeq::description() const
{
    return tr("A self-report version of the Eating Disorder Examination (EDE)");
}


QStringList Edeq::fieldNames() const
{
    auto field_names = strseq(QPREFIX, FIRST_Q, N_QUESTIONS) + QStringList {
        Q_MASS_KG, Q_HEIGHT_M};

    if (isFemale()) {
        field_names += {Q_NUM_PERIODS_MISSED, Q_PILL};
    }

    return field_names;
}

// ============================================================================
// Instance info
// ============================================================================


bool Edeq::isComplete() const
{
    if (anyNull(values(fieldNames()))) {
        return false;
    }

    return true;
}


QStringList Edeq::summary() const
{
    auto rangeScore = [](const QString& description, const QVariant score,
                         const int min, const int max) {
        return QString("%1: <b>%2</b> [%3–%4].").arg(
                    description,
                    QString::number(score.toInt()),
                    QString::number(min),
                    QString::number(max));
    };

    return QStringList{
        rangeScore(TextConst::totalScore(), globalScore(),
                   MIN_SCORE, MAX_SCORE),
        rangeScore(xstring("restraint"), restraint(), MIN_SUBSCALE, MAX_SUBSCALE),
        rangeScore(xstring("eating_concern"), eatingConcern(), MIN_SUBSCALE, MAX_SUBSCALE),
        rangeScore(xstring("shape_concern"), shapeConcern(), MIN_SUBSCALE, MAX_SUBSCALE),
        rangeScore(xstring("weight_concern"), weightConcern(), MIN_SUBSCALE, MAX_SUBSCALE),
    };
}


QVariant Edeq::globalScore() const
{
    QVector<QVariant> subscales = {
        restraint(),
        eatingConcern(),
        shapeConcern(),
        weightConcern(),
    };

    return meanOrNull(subscales);
}

QVariant Edeq::restraint() const
{
    return subscale(RESTRAINT_QUESTIONS);
}


QVariant Edeq::eatingConcern() const
{
    return subscale(EATING_CONCERN_QUESTIONS);
}


QVariant Edeq::shapeConcern() const
{
    return subscale(SHAPE_CONCERN_QUESTIONS);
}


QVariant Edeq::weightConcern() const
{
    return subscale(WEIGHT_CONCERN_QUESTIONS);
}


QVariant Edeq::subscale(QVector<int> questions) const
{
    QVector<QVariant> answers = values(strnumlist(QPREFIX, questions));

    return meanOrNull(answers);
}


QStringList Edeq::detail() const
{
    QStringList lines;

    return lines;
}


OpenableWidget* Edeq::editor(const bool read_only)
{
    const NameValueOptions days_options{
        {xstring("days_option_0"), 0},
        {xstring("days_option_1"), 1},
        {xstring("days_option_2"), 2},
        {xstring("days_option_3"), 3},
        {xstring("days_option_4"), 4},
        {xstring("days_option_5"), 5},
        {xstring("days_option_6"), 6},
    };
    const int days_min_width_px = 50;
    const QVector<int> days_min_option_widths_px = {50, 50, 50, 50, 50, 50, 50};

    const NameValueOptions freq_options{
        {xstring("freq_option_0"), 0},
        {xstring("freq_option_1"), 1},
        {xstring("freq_option_2"), 2},
        {xstring("freq_option_3"), 3},
        {xstring("freq_option_4"), 4},
        {xstring("freq_option_5"), 5},
        {xstring("freq_option_6"), 6},
    };
    const int freq_min_width_px = 50;
    const QVector<int> freq_min_option_widths_px = {50, 50, 50, 50, 50, 50, 50};

    const NameValueOptions how_much_options{
        {xstring("how_much_option_0"), 0},
        {xstring("how_much_option_1"), 1},
        {xstring("how_much_option_2"), 2},
        {xstring("how_much_option_3"), 3},
        {xstring("how_much_option_4"), 4},
        {xstring("how_much_option_5"), 5},
        {xstring("how_much_option_6"), 6},
    };
    const int how_much_min_width_px = 100;
    const QVector<int> how_much_min_option_widths_px = {100, 100, 100, 100, 100, 100, 100};

    auto instructions = new QuHeading(xstring("instructions"));
    auto instructions1_12 = new QuHeading(xstring("q1_12_instructions"));
    auto grid1_12 = buildGrid(1, 12, days_options,
                              xstring("q1_12_heading"));
    grid1_12->setMinimumWidthInPixels(days_min_width_px,
                                      days_min_option_widths_px);

    auto instructions13_18 = new QuHeading(xstring("q13_18_instructions"));
    auto heading13_18 = new QuHeading(xstring("q13_18_heading"));
    auto grid13_18 = new QuGridContainer();
    for (int row = 0; row < 6; row++) {
        const int qnum = row + 13;
        const QString& fieldname = "q" + QString::number(qnum);
        auto number_editor = new QuLineEditInteger(fieldRef(fieldname),
0, 1000); // TODO: Better maximum
        auto question_text = new QuText(xstring(fieldname));
        grid13_18->addCell(QuGridCell(question_text, row, 0));
        grid13_18->addCell(QuGridCell(number_editor, row, 1));
    }
    grid13_18->setColumnStretch(0, 6);
    grid13_18->setColumnStretch(1, 1);

    auto instructions19_21 = new QuHeading(xstring("q19_21_instructions"));
    auto grid19 = buildGrid(19, 19, days_options);
    grid19->setMinimumWidthInPixels(days_min_width_px,
                                    days_min_option_widths_px);
    auto grid20 = buildGrid(20, 20, freq_options);
    grid20->setMinimumWidthInPixels(freq_min_width_px,
                                    freq_min_option_widths_px);

    auto grid21 = buildGrid(21, 21, how_much_options);
    grid21->setMinimumWidthInPixels(how_much_min_width_px,
                                    how_much_min_option_widths_px);
    auto instructions22_28 = new QuHeading(xstring("q22_28_instructions"));
    auto grid22_28 = buildGrid(22, 28, how_much_options, xstring("q22_28_heading"));
    grid22_28->setMinimumWidthInPixels(how_much_min_width_px,
                                       how_much_min_option_widths_px);

    auto mass_text = new QuText(xstring(Q_MASS_KG));
    auto mass_units = new QuUnitSelector(CommonOptions::massUnits());
    auto mass_edit = new QuMass(fieldRef(Q_MASS_KG), mass_units);
    auto height_text = new QuText(xstring(Q_HEIGHT_M));
    auto height_units = new QuUnitSelector(CommonOptions::heightUnits());
    auto height_edit = new QuHeight(fieldRef(Q_HEIGHT_M), height_units);

    QVector<QuElement*> elements{
                    instructions,
                    instructions1_12,
                    grid1_12,
                    instructions13_18,
                    heading13_18,
                    grid13_18,
                    instructions19_21,
                    grid19,
                    grid20,
                    grid21,
                    instructions22_28,
                    grid22_28,
                    mass_text,
                    mass_units,
                    mass_edit,
                    height_text,
                    height_units,
                    height_edit,
    };

    if (isFemale()) {
        FieldRef::GetterFunction get_have_missed_periods = std::bind(&Edeq::getHaveMissedPeriods, this);
        FieldRef::SetterFunction set_have_missed_periods = std::bind(&Edeq::setHaveMissedPeriods, this, std::placeholders::_1);
        m_have_missed_periods_fr = FieldRefPtr(new FieldRef(get_have_missed_periods, set_have_missed_periods, true));
        auto have_missed_periods_edit = (
            new QuMcq(
                m_have_missed_periods_fr,
                CommonOptions::yesNoBoolean()
                )
            );
        auto num_periods_missed_edit = new QuLineEditInteger(fieldRef(Q_NUM_PERIODS_MISSED), 0, 10);
        auto have_missed_periods_grid = questionnairefunc::defaultGridRawPointer(
            {
                {xstring("q_have_missed_periods"), have_missed_periods_edit},
            }, 1, 1);
        elements.append(have_missed_periods_grid);

        m_num_periods_missed_grid = questionnairefunc::defaultGridRawPointer(
            {
                {xstring(Q_NUM_PERIODS_MISSED), num_periods_missed_edit}
            }, 1, 1);
        elements.append(m_num_periods_missed_grid);

        auto pill_edit =
            (new QuMcq(fieldRef(Q_PILL), CommonOptions::yesNoBoolean()));
        auto pill_grid = questionnairefunc::defaultGridRawPointer(
            {{xstring("q_pill"), pill_edit}}, 1, 1);
        elements.append(pill_grid);
    };

    elements.append(new QuText(xstring("thanks")));

    QuPagePtr page((new QuPage(elements))->setTitle(xstring("title_main")));

    m_questionnaire = new Questionnaire(m_app, {page});
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);

    m_have_missed_periods_fr->setValue(valueInt(Q_NUM_PERIODS_MISSED) > 0);

    return m_questionnaire;
}


QVariant Edeq::getHaveMissedPeriods()
{
    return m_have_missed_periods;
}


bool Edeq::setHaveMissedPeriods(const QVariant& value)
{
    const bool changed = value != m_have_missed_periods;

    if (changed) {
        m_have_missed_periods = value;

        const bool have_missed = value.toBool();

        if (!have_missed) {
            setValue(Q_NUM_PERIODS_MISSED, 0);
        }

        m_num_periods_missed_grid->setVisible(have_missed);
    }

    return changed;
}


QuMcqGrid* Edeq::buildGrid(int first_qnum,
                           int last_qnum,
                           const NameValueOptions options,
                           const QString title)
{
    QVector<QuestionWithOneField> q_field_pairs;

    for (int qnum = first_qnum; qnum <= last_qnum; qnum++) {
        const QString& fieldname = "q" + QString::number(qnum);
        const QString& description = xstring(fieldname);

        q_field_pairs.append(QuestionWithOneField(description,
                                                  fieldRef(fieldname)));

    }

    auto grid = new QuMcqGrid(q_field_pairs, options);
    grid->setTitle(title);
    // Repeat options every five lines
    QVector<McqGridSubtitle> subtitles{
        {5, title},
        {10, title},
        {15, title},
    };
    grid->setSubtitles(subtitles);

    const int question_width = 4;
    const QVector<int> option_widths = {1, 1, 1, 1, 1, 1, 1};
    grid->setWidth(question_width, option_widths);
    grid->setQuestionsBold(false);

    return grid;
}
