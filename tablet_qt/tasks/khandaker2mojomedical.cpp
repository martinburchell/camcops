/*
    Copyright (C) 2012-2019 Rudolf Cardinal (rudolf@pobox.com).

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

#include "khandaker2mojomedical.h"
#include "common/cssconst.h"
#include "common/textconst.h"
#include "lib/convert.h"
#include "lib/uifunc.h"
#include "lib/version.h"
#include "questionnairelib/commonoptions.h"
#include "questionnairelib/questionnaire.h"
#include "questionnairelib/qudatetime.h"
#include "questionnairelib/quheading.h"
#include "questionnairelib/qulineeditdouble.h"
#include "questionnairelib/qulineeditinteger.h"
#include "questionnairelib/qumcq.h"
#include "questionnairelib/qupage.h"
#include "questionnairelib/quspacer.h"
#include "questionnairelib/qutext.h"
#include "questionnairelib/qutextedit.h"
#include "tasklib/taskfactory.h"


const QString Khandaker2MojoMedical::KHANDAKER2MOJOMEDICAL_TABLENAME(
    "khandaker_2_mojomedical");

const QString Q_XML_PREFIX = "q_";

// Section 1: General Information
const QString FN_DIAGNOSIS("diagnosis");
const QString FN_DIAGNOSIS_DATE("diagnosis_date");
const QString FN_HAS_FIBROMYALGIA("has_fibromyalgia");
const QString FN_IS_PREGNANT("is_pregnant");
const QString FN_HAS_INFECTION_PAST_MONTH("has_infection_past_month");
const QString FN_HAD_INFECTION_TWO_MONTHS_PRECEDING("had_infection_two_months_preceding");
const QString FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE("has_alcohol_substance_dependence");
const QString FN_SMOKING_STATUS("smoking_status");
const QString FN_ALCOHOL_UNITS_PER_WEEK("alcohol_units_per_week");

// Section 2: Medical History
const QString FN_DEPRESSION("depression");
const QString FN_BIPOLAR_DISORDER("bipolar_disorder");
const QString FN_SCHIZOPHRENIA("schizophrenia");
const QString FN_AUTISM("autism");
const QString FN_PTSD("ptsd");
const QString FN_ANXIETY("anxiety");
const QString FN_PERSONALITY_DISORDER("personality_disorder");
const QString FN_INTELLECTUAL_DISABILITY("intellectual_disability");
const QString FN_OTHER_MENTAL_ILLNESS("other_mental_illness");
const QString FN_OTHER_MENTAL_ILLNESS_DETAILS("other_mental_illness_details");
const QString FN_HOSPITALISED_IN_LAST_YEAR("hospitalised_in_last_year");
const QString FN_HOSPITALISATION_DETAILS("hospitalisation_details");

// Section 3: Family history
const QString FN_FAMILY_DEPRESSION("family_depression");
const QString FN_FAMILY_BIPOLAR_DISORDER("family_bipolar_disorder");
const QString FN_FAMILY_SCHIZOPHRENIA("family_schizophrenia");
const QString FN_FAMILY_AUTISM("family_autism");
const QString FN_FAMILY_PTSD("family_ptsd");
const QString FN_FAMILY_ANXIETY("family_anxiety");
const QString FN_FAMILY_PERSONALITY_DISORDER("family_personality_disorder");
const QString FN_FAMILY_INTELLECTUAL_DISABILITY("family_intellectual_disability");
const QString FN_FAMILY_OTHER_MENTAL_ILLNESS("family_other_mental_illness");
const QString FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS("family_other_mental_illness_details");

const QStringList MANDATORY_FIELDNAMES{
    FN_DIAGNOSIS,
    FN_DIAGNOSIS_DATE,
    FN_HAS_FIBROMYALGIA,
    FN_IS_PREGNANT,
    FN_HAS_INFECTION_PAST_MONTH,
    FN_HAD_INFECTION_TWO_MONTHS_PRECEDING,
    FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE,
    FN_SMOKING_STATUS,
    FN_ALCOHOL_UNITS_PER_WEEK,

    FN_DEPRESSION,
    FN_BIPOLAR_DISORDER,
    FN_SCHIZOPHRENIA,
    FN_AUTISM,
    FN_PTSD,
    FN_ANXIETY,
    FN_PERSONALITY_DISORDER,
    FN_INTELLECTUAL_DISABILITY,
    FN_OTHER_MENTAL_ILLNESS,
    FN_HOSPITALISED_IN_LAST_YEAR,

    FN_FAMILY_DEPRESSION,
    FN_FAMILY_BIPOLAR_DISORDER,
    FN_FAMILY_SCHIZOPHRENIA,
    FN_FAMILY_AUTISM,
    FN_FAMILY_PTSD,
    FN_FAMILY_ANXIETY,
    FN_FAMILY_PERSONALITY_DISORDER,
    FN_FAMILY_INTELLECTUAL_DISABILITY,
    FN_FAMILY_OTHER_MENTAL_ILLNESS,
};

const QMap<QString, QString> DETAILS_FIELDS{
    {FN_OTHER_MENTAL_ILLNESS, FN_OTHER_MENTAL_ILLNESS_DETAILS},
    {FN_HOSPITALISED_IN_LAST_YEAR, FN_HOSPITALISATION_DETAILS},
    {FN_FAMILY_OTHER_MENTAL_ILLNESS, FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS},
};

void initializeKhandaker2MojoMedical(TaskFactory& factory)
{
    static TaskRegistrar<Khandaker2MojoMedical> registered(factory);
}


Khandaker2MojoMedical::Khandaker2MojoMedical(
        CamcopsApp& app, DatabaseManager& db, const int load_pk) :
    Task(app, db, KHANDAKER2MOJOMEDICAL_TABLENAME,
         false, false, false),  // ... anon, clin, resp
    m_questionnaire(nullptr)
{
    // Section 1: General Information
    addField(FN_DIAGNOSIS, QVariant::Int);
    addField(FN_DIAGNOSIS_DATE, QVariant::Date);
    addField(FN_HAS_FIBROMYALGIA, QVariant::Bool);
    addField(FN_IS_PREGNANT, QVariant::Bool);
    addField(FN_HAS_INFECTION_PAST_MONTH, QVariant::Bool);
    addField(FN_HAD_INFECTION_TWO_MONTHS_PRECEDING, QVariant::Bool);
    addField(FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE, QVariant::Bool);
    addField(FN_SMOKING_STATUS, QVariant::Int);
    addField(FN_ALCOHOL_UNITS_PER_WEEK, QVariant::Double);

    // Section 2: Medical History
    addField(FN_DEPRESSION, QVariant::Bool);
    addField(FN_BIPOLAR_DISORDER, QVariant::Bool);
    addField(FN_SCHIZOPHRENIA, QVariant::Bool);
    addField(FN_AUTISM, QVariant::Bool);
    addField(FN_PTSD, QVariant::Bool);
    addField(FN_ANXIETY, QVariant::Bool);
    addField(FN_PERSONALITY_DISORDER, QVariant::Bool);
    addField(FN_INTELLECTUAL_DISABILITY, QVariant::Bool);
    addField(FN_OTHER_MENTAL_ILLNESS, QVariant::Bool);
    addField(FN_OTHER_MENTAL_ILLNESS_DETAILS, QVariant::String);
    addField(FN_HOSPITALISED_IN_LAST_YEAR, QVariant::Bool);
    addField(FN_HOSPITALISATION_DETAILS, QVariant::String);

    // Section 3: Family history
    addField(FN_FAMILY_DEPRESSION, QVariant::Bool);
    addField(FN_FAMILY_BIPOLAR_DISORDER, QVariant::Bool);
    addField(FN_FAMILY_SCHIZOPHRENIA, QVariant::Bool);
    addField(FN_FAMILY_AUTISM, QVariant::Bool);
    addField(FN_FAMILY_PTSD, QVariant::Bool);
    addField(FN_FAMILY_ANXIETY, QVariant::Bool);
    addField(FN_FAMILY_PERSONALITY_DISORDER, QVariant::Bool);
    addField(FN_FAMILY_INTELLECTUAL_DISABILITY, QVariant::Bool);
    addField(FN_FAMILY_OTHER_MENTAL_ILLNESS, QVariant::Bool);
    addField(FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS, QVariant::String);

    load(load_pk);  // MUST ALWAYS CALL from derived Task constructor.
}



// ============================================================================
// Class info
// ============================================================================

QString Khandaker2MojoMedical::shortname() const
{
    return "Khandaker_2_MOJOMedical";
}


QString Khandaker2MojoMedical::longname() const
{
    return tr("Khandaker GM — 2 MOJO Study — Medical Questionnaire");
}


QString Khandaker2MojoMedical::description() const
{
    return tr("Medical Questionnaire for MOJO Study.");
}


// ============================================================================
// Instance info
// ============================================================================

bool Khandaker2MojoMedical::isComplete() const
{
    for (const QString fieldname: MANDATORY_FIELDNAMES) {
        if (valueIsNull(fieldname)) {
            return false;
        }

        if (DETAILS_FIELDS.contains(fieldname)) {
            if (valueBool(fieldname) &&
                valueIsNullOrEmpty(DETAILS_FIELDS.value(fieldname))) {
                return false;
                }
        }
    }

    return true;
}


QStringList Khandaker2MojoMedical::summary() const
{
    return QStringList{TextConst::noSummarySeeFacsimile()};
}


QStringList Khandaker2MojoMedical::detail() const
{
    QStringList lines;

    for (const QString fieldname : MANDATORY_FIELDNAMES) {
        lines.append(xstring(Q_XML_PREFIX + fieldname));
        lines.append(QString("<b>%1</b>").arg(prettyValue(fieldname)));

        if (DETAILS_FIELDS.contains(fieldname) && valueBool(fieldname)) {
            const QString details_fieldname = DETAILS_FIELDS.value(fieldname);
            lines.append(xstring(Q_XML_PREFIX + details_fieldname));
            lines.append(QString("<b>%1</b>").arg(
                             prettyValue(details_fieldname)));

        }
    }

    return completenessInfo() + lines;
}


OpenableWidget* Khandaker2MojoMedical::editor(const bool read_only)
{
    QuPagePtr page(new QuPage);

    auto textQuestion = [this, &page](const QString &fieldname) -> void {
        page->addElement(new QuText(xstring(Q_XML_PREFIX + fieldname)));
        page->addElement(new QuTextEdit(fieldRef(fieldname)));
        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE,
                                            uiconst::BIGSPACE)));
    };

    auto getOptions = [this](const QString &fieldname,
                             int num_options) -> NameValueOptions {
        NameValueOptions options;

        for (int i = 0; i < num_options; i++) {
            const QString name = getOptionName(fieldname, i);
            options.append(NameValuePair(name, i));
        }

        return options;
    };

    auto multiChoiceQuestion = [this, &page, getOptions](const QString &fieldname,
                                             int num_options) -> void {
        page->addElement(new QuText(xstring(Q_XML_PREFIX + fieldname)));

        FieldRefPtr fieldref = fieldRef(fieldname);
        QuMcq* mcq = new QuMcq(fieldref, getOptions(fieldname, num_options));
        mcq->setHorizontal(true);
        page->addElement(mcq);
        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE,
                                            uiconst::BIGSPACE)));
    };

    auto dateQuestion = [this, &page](const QString &fieldname) -> void {
        page->addElement(new QuText(xstring(Q_XML_PREFIX + fieldname)));

        auto date_time = new QuDateTime(fieldRef(fieldname));
        date_time->setOfferNowButton(true);
        page->addElement(date_time);
        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE,
                                            uiconst::BIGSPACE)));
    };

    auto yesNoQuestion = [this, &page](const QString &fieldname) -> void {
        page->addElement(new QuText(xstring(Q_XML_PREFIX + fieldname)));

        FieldRefPtr fieldref = fieldRef(fieldname);
        QuMcq* mcq = new QuMcq(fieldref, CommonOptions::noYesBoolean());
        mcq->setHorizontal(true);
        page->addElement(mcq);
        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE,
                                            uiconst::BIGSPACE)));

    };

    auto doubleQuestion = [this, &page](const QString &fieldname) -> void {
        page->addElement(new QuText(xstring(Q_XML_PREFIX + fieldname)));
        page->addElement(new QuLineEditDouble(fieldRef(fieldname)));
        page->addElement(new QuSpacer(QSize(uiconst::BIGSPACE,
                                            uiconst::BIGSPACE)));
    };

    page->setTitle(description());
    page->addElement(new QuHeading(xstring("title")));
    page->addElement(new QuHeading(xstring("general_information_title")));

    multiChoiceQuestion(FN_DIAGNOSIS, 3);
    dateQuestion(FN_DIAGNOSIS_DATE);

    page->addElement(new QuHeading(xstring("medical_history_title")));
    yesNoQuestion(FN_HAS_FIBROMYALGIA);
    yesNoQuestion(FN_IS_PREGNANT);
    yesNoQuestion(FN_HAS_INFECTION_PAST_MONTH);
    yesNoQuestion(FN_HAD_INFECTION_TWO_MONTHS_PRECEDING);
    yesNoQuestion(FN_HAS_ALCOHOL_SUBSTANCE_DEPENDENCE);
    multiChoiceQuestion(FN_SMOKING_STATUS, 3);
    doubleQuestion(FN_ALCOHOL_UNITS_PER_WEEK);

    page->addElement(new QuHeading(xstring("medical_history_subtitle")));
    yesNoQuestion(FN_DEPRESSION);
    yesNoQuestion(FN_BIPOLAR_DISORDER);
    yesNoQuestion(FN_SCHIZOPHRENIA);
    yesNoQuestion(FN_AUTISM);
    yesNoQuestion(FN_PTSD);
    yesNoQuestion(FN_ANXIETY);
    yesNoQuestion(FN_PERSONALITY_DISORDER);
    yesNoQuestion(FN_INTELLECTUAL_DISABILITY);
    yesNoQuestion(FN_OTHER_MENTAL_ILLNESS);
    textQuestion(FN_OTHER_MENTAL_ILLNESS_DETAILS);
    yesNoQuestion(FN_HOSPITALISED_IN_LAST_YEAR);
    textQuestion(FN_HOSPITALISATION_DETAILS);

    page->addElement(new QuHeading(xstring("family_history_title")));
    page->addElement(new QuHeading(xstring("family_history_subtitle")));
    yesNoQuestion(FN_FAMILY_DEPRESSION);
    yesNoQuestion(FN_FAMILY_BIPOLAR_DISORDER);
    yesNoQuestion(FN_FAMILY_SCHIZOPHRENIA);
    yesNoQuestion(FN_FAMILY_AUTISM);
    yesNoQuestion(FN_FAMILY_PTSD);
    yesNoQuestion(FN_FAMILY_ANXIETY);
    yesNoQuestion(FN_FAMILY_PERSONALITY_DISORDER);
    yesNoQuestion(FN_FAMILY_INTELLECTUAL_DISABILITY);
    yesNoQuestion(FN_FAMILY_OTHER_MENTAL_ILLNESS);
    textQuestion(FN_FAMILY_OTHER_MENTAL_ILLNESS_DETAILS);

    for (auto fieldname : DETAILS_FIELDS.keys()) {
        FieldRefPtr fieldref = fieldRef(fieldname);

        connect(fieldref.data(), &FieldRef::valueChanged,
                this, &Khandaker2MojoMedical::updateMandatory);
    }

    QVector<QuPagePtr> pages{page};

    m_questionnaire = new Questionnaire(m_app, pages);
    m_questionnaire->setType(QuPage::PageType::Patient);
    m_questionnaire->setReadOnly(read_only);



    updateMandatory();

    return m_questionnaire;
}


QString Khandaker2MojoMedical::getOptionName(
    const QString &fieldname, const int index) const
{
    return xstring(QString("%1_%2").arg(fieldname).arg(index));
}


// ============================================================================
// Signal handlers
// ============================================================================

void Khandaker2MojoMedical::updateMandatory()
{
    // This could be more efficient with lots of signal handlers, but...

    for (auto fieldname : DETAILS_FIELDS.keys()) {
        if (valueIsNull(fieldname)) {
            continue;
        }

        const bool mandatory = valueBool(fieldname);
        const QString details_fieldname = DETAILS_FIELDS.value(fieldname);
        fieldRef(details_fieldname)->setMandatory(mandatory);

        m_questionnaire->setVisibleByTag(details_fieldname, mandatory);
    }
}
