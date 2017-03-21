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
#include <QPointer>
#include <QString>
#include "tasklib/task.h"

class CamcopsApp;
class OpenableWidget;
class TaskFactory;

void initializeCape42(TaskFactory& factory);


class Cape42 : public Task
{
    Q_OBJECT
public:
    Cape42(CamcopsApp& app, const QSqlDatabase& db,
           int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    virtual QString infoFilenameStem() const;
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
    int distressScore(const QList<int>& questions) const;
    int frequencyScore(const QList<int>& questions) const;
    bool questionComplete(int q) const;
    // ------------------------------------------------------------------------
    // Signal handlers
    // ------------------------------------------------------------------------
public slots:
    void frequencyChanged(const FieldRef* fieldref);
protected:
    bool needDistress(int q);
    void setDistressItems(int q);
    QPointer<Questionnaire> m_questionnaire;
    QMap<int, FieldRefPtr> m_distress_fieldrefs;
};
