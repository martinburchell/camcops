#include "quspinboxinteger.h"
#include <QSpinBox>
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"


QuSpinBoxInteger::QuSpinBoxInteger(FieldRefPtr fieldref, int minimum,
                                   int maximum) :
    m_fieldref(fieldref),
    m_minimum(minimum),
    m_maximum(maximum)
{
    Q_ASSERT(m_fieldref);
    connect(m_fieldref.data(), &FieldRef::valueChanged,
            this, &QuSpinBoxInteger::fieldValueChanged);
    connect(m_fieldref.data(), &FieldRef::mandatoryChanged,
            this, &QuSpinBoxInteger::fieldValueChanged);
}


void QuSpinBoxInteger::setFromField()
{
    fieldValueChanged(m_fieldref.data(), nullptr);
    // special; pretend "it didn't come from us" to disable the efficiency
    // check in fieldValueChanged
}


QPointer<QWidget> QuSpinBoxInteger::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = questionnaire->readOnly();
    m_spinbox = new QSpinBox();
    m_spinbox->setEnabled(!read_only);
    m_spinbox->setRange(m_minimum, m_maximum);
    m_spinbox->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    // QSpinBox has two signals named valueChanged, differing only
    // in the parameter they pass (int versus QString&). You get
    // "no matching function for call to ... unresolved overloaded function
    // type..."
    // Disambiguate like this:
    void (QSpinBox::*vc_signal)(int) = &QSpinBox::valueChanged;
    if (!read_only) {
        connect(m_spinbox.data(), vc_signal,
                this, &QuSpinBoxInteger::widgetValueChanged);
    }
    setFromField();
    return QPointer<QWidget>(m_spinbox);
}


FieldRefPtrList QuSpinBoxInteger::fieldrefs() const
{
    return FieldRefPtrList{m_fieldref};
}

void QuSpinBoxInteger::widgetValueChanged(int value)
{
    bool changed = m_fieldref->setValue(value, this);  // Will trigger valueChanged
    if (changed) {
        emit elementValueChanged();
    }
}


void QuSpinBoxInteger::fieldValueChanged(const FieldRef* fieldref,
                                         const QObject* originator)
{
    if (!m_spinbox) {
        return;
    }
    UiFunc::setPropertyMissing(m_spinbox, fieldref->missingInput());
    if (originator != this) {
        const QSignalBlocker blocker(m_spinbox);
        m_spinbox->setValue(fieldref->valueInt());
    }
}
