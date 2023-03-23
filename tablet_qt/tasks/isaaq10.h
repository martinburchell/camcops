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

#pragma once
#include <QPointer>

#include "taskxtra/isaaqcommon.h"
#include "tasklib/task.h"

class CamcopsApp;

void initializeIsaaq10(TaskFactory& factory);

class Isaaq10 : public IsaaqCommon
{
    Q_OBJECT
public:
    Isaaq10(CamcopsApp& app, DatabaseManager& db,
            int load_pk = dbconst::NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // Class overrides
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString description() const override;
    virtual bool prohibitsCommercial() const override { return true; }
    virtual void upgradeDatabase(const Version& old_version,
                                 const Version& new_version) override;

public:
    static const QString ISAAQ10_TABLENAME;
protected:
    QStringList fieldNames() const override;
    QVector<QuElement*> buildElements() override;
};
