#include "qubutton.h"
#include "lib/uifunc.h"
#include "questionnairelib/questionnaire.h"
#include "widgets/clickablelabelwordwrapwide.h"
#include "widgets/imagebutton.h"


QuButton::QuButton(const QString& label,
                   const CallbackFunction& callback) :
    m_label(label),
    m_callback(callback),
    m_active(true)
{
}


QuButton::QuButton(const QString& icon_filename, bool filename_is_camcops_stem,
                   bool alter_unpressed_image,
                   const CallbackFunction& callback) :
    m_icon_filename(icon_filename),
    m_filename_is_camcops_stem(filename_is_camcops_stem),
    m_alter_unpressed_image(alter_unpressed_image),
    m_callback(callback),
    m_active(true)
{
}


QuButton* QuButton::setActive(bool active)
{
    m_active = active;
    return this;
}


QPointer<QWidget> QuButton::makeWidget(Questionnaire* questionnaire)
{
    bool read_only = !m_active || questionnaire->readOnly();
    QAbstractButton* button;
    if (!m_label.isEmpty()) {
        // Text
        button = new ClickableLabelWordWrapWide(m_label);
        if (read_only) {
            button->setDisabled(true);
        }
    } else {
        // Image
        button = new ImageButton(m_icon_filename, m_filename_is_camcops_stem,
                                 m_alter_unpressed_image, read_only);
    }
    if (!read_only) {
        connect(button, &QAbstractButton::clicked,
                this, &QuButton::clicked);
    }
    return QPointer<QWidget>(button);
}


void QuButton::clicked()
{
    m_callback();
}
