/*
    Copyright (C) 2012-2020 Rudolf Cardinal (rudolf@pobox.com).

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
#include <QPointer>
#include <QString>
#include "questionnairelib/namevalueoptions.h"
#include "questionnairelib/questionwithonefield.h"
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class Questionnaire;
class TaskFactory;

void initializeWsas(TaskFactory& factory);


class Wsas : public Task
{
    Q_OBJECT
public:
    Wsas(CamcopsApp& app, DatabaseManager& db,
         int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;
    virtual TaskImplementationType implementationType() const override {
        return TaskImplementationType::UpgradableSkeleton;
    }
    // ------------------------------------------------------------------------
    // Instance overrides
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QStringList summary() const override;
    virtual QStringList detail() const override;
    virtual OpenableWidget* editor(bool read_only = false) override;
    // ------------------------------------------------------------------------
    // Task-specific calculations
    // ------------------------------------------------------------------------
    int totalScore() const;
    int maxScore() const;
    // ------------------------------------------------------------------------
    // Signal handlers
    // ------------------------------------------------------------------------
public slots:
    void workChanged();
    void orientationChanged(Qt::ScreenOrientation orientation);

protected:
    QPointer<Questionnaire> m_questionnaire;
public:
    static const QString WSAS_TABLENAME;

private:
    NameValueOptions m_options;
    QVector<QuestionWithOneField> m_q1_fields;
    QVector<QuestionWithOneField> m_other_q_fields;
    void refreshQuestionnaire();
    void rebuildPage(QuPage* page);
};
