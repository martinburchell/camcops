#pragma once
#include <QString>
#include "common/camcopsapp.h"
#include "tasklib/task.h"
#include "tasklib/taskfactory.h"


class Phq9 : public Task
{
public:
    Phq9(const QSqlDatabase& db, int load_pk = NONEXISTENT_PK);
    // ------------------------------------------------------------------------
    // General info
    // ------------------------------------------------------------------------
    virtual QString shortname() const override;
    virtual QString longname() const override;
    virtual QString menusubtitle() const override;
    // ------------------------------------------------------------------------
    // Specific info
    // ------------------------------------------------------------------------
    virtual bool isComplete() const override;
    virtual QString getSummary() const override;
    virtual QString getDetail() const override;
    virtual void edit(CamcopsApp& app) override;
};

void initializePhq9(TaskFactory& factory);