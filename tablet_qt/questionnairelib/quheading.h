#pragma once
#include <QString>
#include "qutext.h"


class QuHeading : public QuText
{
    Q_OBJECT
public:
    QuHeading(const QString& text);
    QuHeading(FieldRefPtr fieldref);
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
};
