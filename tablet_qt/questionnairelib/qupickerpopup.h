#pragma once
#include "lib/fieldref.h"
#include "namevalueoptions.h"
#include "quelement.h"

class ClickableLabel;


class QuPickerPopup : public QuElement
{
    Q_OBJECT
public:
    QuPickerPopup(FieldRefPtr fieldref, const NameValueOptions& options);
    QuPickerPopup* setPopupTitle(const QString& popup_title);
    void setFromField();
protected:
    virtual QPointer<QWidget> makeWidget(Questionnaire* questionnaire) override;
    virtual bool complete() const override;
protected slots:
    void clicked();
    void valueChanged(const QVariant& value);
protected:
    FieldRefPtr m_fieldref;
    NameValueOptions m_options;
    QString m_popup_title;
    QPointer<ClickableLabel> m_label;
};
