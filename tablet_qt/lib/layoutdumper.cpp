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

#include "layoutdumper.h"
#include <iostream>
#include <sstream>
#include <string>
#include <stdio.h>
#include <QDebug>
#include <QScrollArea>
#include <QString>
#include <QStringBuilder>
#include <QtWidgets/QLayout>
#include <QtWidgets/QWidget>
#include "lib/convert.h"
#include "lib/uifunc.h"

namespace layoutdumper {

const QString NULL_WIDGET_STRING("<null_widget>");


QString toString(const QSizePolicy::Policy& policy)
{
    switch (policy) {
    case QSizePolicy::Fixed: return "Fixed";
    case QSizePolicy::Minimum: return "Minimum";
    case QSizePolicy::Maximum: return "Maximum";
    case QSizePolicy::Preferred: return "Preferred";
    case QSizePolicy::MinimumExpanding: return "MinimumExpanding";
    case QSizePolicy::Expanding: return "Expanding";
    case QSizePolicy::Ignored: return "Ignored";
    }
    return "unknown_QSizePolicy";
}


QString toString(const QSizePolicy& policy)
{
    QString result = QString("(%1, %2) [hasHeightForWidth=%3]")
            .arg(toString(policy.horizontalPolicy()))
            .arg(toString(policy.verticalPolicy()))
            .arg(toString(policy.hasHeightForWidth()));
    return result;
}


QString toString(QLayout::SizeConstraint constraint)
{
    switch (constraint) {
    case QLayout::SetDefaultConstraint: return "SetDefaultConstraint";
    case QLayout::SetNoConstraint: return "SetNoConstraint";
    case QLayout::SetMinimumSize: return "SetMinimumSize";
    case QLayout::SetFixedSize: return "SetFixedSize";
    case QLayout::SetMaximumSize: return "SetMaximumSize";
    case QLayout::SetMinAndMaxSize: return "SetMinAndMaxSize";
    }
    return "unknown_SizeConstraint";
}


QString toString(const Qt::Alignment& alignment)
{
    QStringList elements;

    if (alignment & Qt::AlignLeft) {
        elements.append("AlignLeft");
    }
    if (alignment & Qt::AlignRight) {
        elements.append("AlignRight");
    }
    if (alignment & Qt::AlignHCenter) {
        elements.append("AlignHCenter");
    }
    if (alignment & Qt::AlignJustify) {
        elements.append("AlignJustify");
    }
    if (alignment & Qt::AlignAbsolute) {
        elements.append("AlignAbsolute");
    }
    if ((alignment & Qt::AlignHorizontal_Mask) == 0) {
        elements.append("<horizontal_none>");
    }

    if (alignment & Qt::AlignTop) {
        elements.append("AlignTop");
    }
    if (alignment & Qt::AlignBottom) {
        elements.append("AlignBottom");
    }
    if (alignment & Qt::AlignVCenter) {
        elements.append("AlignVCenter");
    }
    if (alignment & Qt::AlignBaseline) {
        elements.append("AlignBaseline");
    }
    if ((alignment & Qt::AlignVertical_Mask) == 0) {
        elements.append("<vertical_none>");
    }

    return elements.join(" | ");
}


QString toString(const void* pointer)
{
    return convert::prettyPointer(pointer);
}


QString toString(bool boolean)
{
    return boolean ? "true" : "false";
}


QString getWidgetDescriptor(const QWidget* w)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    return QString("%1<%2 '%3'>")
            .arg(w->metaObject()->className())
            .arg(toString((void*)w))
            .arg(w->objectName());
}


QString getWidgetInfo(const QWidget* w, const DumperConfig& config)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }

    const QRect& geom = w->geometry();

    // Can't have >9 arguments to QString arg() system.
    // Using QStringBuilder with % leads to more type faff.
    QStringList elements;
    elements.append(getWidgetDescriptor(w));
    elements.append(w->isVisible() ? "visible" : "HIDDEN");
    elements.append(QString("pos[DOWN] (%1, %2)")
                    .arg(geom.x())
                    .arg(geom.y()));
    elements.append(QString("size[DOWN] (%1 x %2)")
                    .arg(geom.width())
                    .arg(geom.height()));
    elements.append(QString("hasHeightForWidth()[UP] %1")
                    .arg(w->hasHeightForWidth() ? "true" : "false"));
    elements.append(QString("heightForWidth(%1)[UP] %2")
                    .arg(geom.width())
                    .arg(w->heightForWidth(geom.width())));
    elements.append(QString("minimumSize (%1 x %2)")
                    .arg(w->minimumSize().width())
                    .arg(w->minimumSize().height()));
    elements.append(QString("maximumSize (%1 x %2)")
                    .arg(w->maximumSize().width())
                    .arg(w->maximumSize().height()));
    elements.append(QString("sizeHint[UP] (%1 x %2)")
                    .arg(w->sizeHint().width())
                    .arg(w->sizeHint().height()));
    elements.append(QString("minimumSizeHint[UP] (%1 x %2)")
                    .arg(w->minimumSizeHint().width())
                    .arg(w->minimumSizeHint().height()));
    elements.append(QString("sizePolicy[UP] %1")
                    .arg(toString(w->sizePolicy())));
    elements.append(QString("stylesheet: %1")
                    .arg(w->styleSheet().isEmpty() ? "false" : "true"));

    if (config.show_widget_attributes) {
        elements.append(QString("attributes: [%1]")
                        .arg(getWidgetAttributeInfo(w)));
    }

    if (config.show_widget_properties) {
        QString properties = getDynamicProperties(w);
        if (!properties.isEmpty()) {
            elements.append(QString("properties: [%1]").arg(properties));
        }
    }

    if (config.show_widget_stylesheets) {
        elements.append(QString("stylesheet: %1").arg(w->styleSheet()));
    }

    if (geom.width() < w->minimumSize().width() ||
            geom.height() < w->minimumSize().height()) {
        elements.append("[BUG? size < minimumSize()]");
    }
    if (geom.width() < w->minimumSizeHint().width() ||
            geom.height() < w->minimumSizeHint().height()) {
        elements.append("[WARNING: size < minimumSizeHint()]");
    }
    if (w->hasHeightForWidth() &&
            geom.height() < w->heightForWidth(geom.width())) {
        elements.append("[WARNING: height < heightForWidth(width)]");
    }

    return elements.join(", ");
}


QString getWidgetAttributeInfo(const QWidget* w)
{
    // http://doc.qt.io/qt-5/qt.html#WidgetAttribute-enum
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    QStringList elements;
    elements.append(QString("WA_NoSystemBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_NoSystemBackground)));
    elements.append(QString("WA_OpaquePaintEvent %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_OpaquePaintEvent)));
    elements.append(QString("WA_SetStyle %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_SetStyle)));
    elements.append(QString("WA_StyleSheet %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_StyleSheet)));
    elements.append(QString("WA_TranslucentBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_TranslucentBackground)));
    elements.append(QString("WA_StyledBackground %1").arg(
        w->testAttribute(Qt::WidgetAttribute::WA_StyledBackground)));
    return elements.join(", ");
}


QString getDynamicProperties(const QWidget* w)
{
    if (!w) {
        return NULL_WIDGET_STRING;
    }
    QStringList elements;
    QList<QByteArray> property_names = w->dynamicPropertyNames();
    for (const QByteArray& arr : property_names) {
        QString name(arr);
        QVariant value = w->property(arr);
        QString value_string = uifunc::escapeString(value.toString());
        elements.append(QString("%1=%2").arg(name).arg(value_string));
    }
    return elements.join(", ");
}


QString getLayoutInfo(const QLayout* layout)
{
    if (!layout) {
        return "null_layout";
    }
    QMargins margins = layout->contentsMargins();
    QSize sizehint = layout->sizeHint();
    QSize minsize = layout->minimumSize();
    QSize maxsize = layout->maximumSize();
    QString name = layout->metaObject()->className();
    QWidget* parent = layout->parentWidget();
    // usually unhelpful (blank): layout->objectName()
    QStringList elements;
    elements.append(name);
    elements.append(QString("constraint %1")
                    .arg(toString(layout->sizeConstraint())));
    elements.append(QString("minimumSize[UP] (%1 x %2)")
                    .arg(minsize.width())
                    .arg(minsize.height()));
    elements.append(QString("sizeHint[UP] (%1 x %2)")
                    .arg(sizehint.width())
                    .arg(sizehint.height()));
    elements.append(QString("maximumSize[UP] (%1 x %2)")
                    .arg(maxsize.width())
                    .arg(maxsize.height()));
    elements.append(QString("hasHeightForWidth[UP] %3")
                    .arg(toString(layout->hasHeightForWidth())));
    elements.append(QString("margin (l=%1,t=%2,r=%3,b=%4)")
                    .arg(margins.left())
                    .arg(margins.top())
                    .arg(margins.right())
                    .arg(margins.bottom()));
    elements.append(QString("spacing[UP] %1")
                    .arg(layout->spacing()));

    if (parent) {
        QSize parent_size = parent->size();
        int parent_width = parent_size.width();
        elements.append(QString("heightForWidth(%1)[UP] %2")
                        .arg(parent_width)
                        .arg(layout->heightForWidth(parent_width)));
        elements.append(QString("minimumHeightForWidth(%1)[UP] %2")
                        .arg(parent_width)
                        .arg(layout->minimumHeightForWidth(parent_width)));
        if (parent_width < minsize.width() ||
                parent_size.height() < minsize.height()) {
            elements.append("[WARNING: parent->size() < this->minimumSize()]");
        }
    }
    return elements.join(", ");
}


QString getSpacerInfo(QSpacerItem* si)
{
    const QRect& geom = si->geometry();
    QSize si_hint = si->sizeHint();
    const QLayout* si_layout = si->layout();
    QStringList elements;
    elements.append("QSpacerItem");
    elements.append(QString("pos[DOWN] (%1, %2)")
                    .arg(geom.x())
                    .arg(geom.y()));
    elements.append(QString("size[DOWN] (%1 x %2)")
                    .arg(geom.width())
                    .arg(geom.height()));
    elements.append(QString("sizeHint (%1 x %2)")
                    .arg(si_hint.width())
                    .arg(si_hint.height()));
    elements.append(QString("sizePolicy %1")
                    .arg(toString(si->sizePolicy())));
    elements.append(QString("constraint %1 [alignment %2]")
                    .arg(si_layout ? toString(si_layout->sizeConstraint())
                                   : "<no_layout>")
                    .arg(toString(si->alignment())));
    return elements.join(", ");
}


QString paddingSpaces(int level, int spaces_per_level)
{
    return QString(level * spaces_per_level, ' ');
}


QList<const QWidget*> dumpLayoutAndChildren(QDebug& os,
                                            const QLayout* layout,
                                            int level,
                                            const DumperConfig& config)
{
    QString padding = paddingSpaces(level, config.spaces_per_level);
    QString next_padding = paddingSpaces(level + 1, config.spaces_per_level);
    QList<const QWidget*> dumped_children;

    os << padding << "Layout: " << getLayoutInfo(layout);

    const QBoxLayout* box_layout = dynamic_cast<const QBoxLayout*>(layout);
    if (box_layout) {
        os << ", spacing " <<  box_layout->spacing();
    }
    os << "\n";

    if (layout->isEmpty()) {
        os << padding << "... empty layout\n";
    } else {
        int num_items = layout->count();
        for (int i = 0; i < num_items; i++) {
            QLayoutItem* layout_item = layout->itemAt(i);
            QLayout* child_layout = layout_item->layout();
            QWidgetItem* wi = dynamic_cast<QWidgetItem*>(layout_item);
            QSpacerItem* si = dynamic_cast<QSpacerItem*>(layout_item);
            if (wi && wi->widget()) {
                QString alignment = QString(" [alignment from layout: %1]")
                        .arg(toString(wi->alignment()));
                dumped_children.append(
                    dumpWidgetAndChildren(os, wi->widget(), level + 1,
                                          alignment, config));
            } else if (child_layout) {
                dumped_children.append(
                    dumpLayoutAndChildren(os, child_layout, level + 1,
                                          config));
            } else if (si) {
                os << next_padding << getSpacerInfo(si) << "\n";
            } else {
                os << next_padding << "<unknown_QLayoutItem>\n";
            }
        }
    }
    return dumped_children;
}


QList<const QWidget*> dumpWidgetAndChildren(QDebug& os,
                                            const QWidget* w,
                                            int level,
                                            const QString& alignment,
                                            const DumperConfig& config)
{
    QString padding = paddingSpaces(level, config.spaces_per_level);

    os << padding
       << getWidgetInfo(w, config)
       << alignment << "\n";

    QList<const QWidget*> dumped_children;
    dumped_children.append(w);

    QLayout* layout = w->layout();
    if (layout) {
        dumped_children.append(
            dumpLayoutAndChildren(os, layout, level + 1, config));
    }

    // Scroll areas contain but aren't necessarily the parents of their widgets
    // However, they contain a 'qt_scrollarea_viewport' widget that is.
    const QScrollArea* scroll = dynamic_cast<const QScrollArea*>(w);
    if (scroll) {
        dumped_children.append(
            dumpWidgetAndChildren(os, scroll->viewport(), level + 1, "",
                                  config));
    }

    // now output any child widgets that weren't dumped as part of the layout
    QList<QWidget*> widgets = w->findChildren<QWidget*>(
                QString(), Qt::FindDirectChildrenOnly);
    // Search options: FindDirectChildrenOnly or FindChildrenRecursively.
    QList<QWidget*> undumped_children;
    foreach (QWidget* child, widgets) {
        if (!dumped_children.contains(child)) {
            undumped_children.push_back(child);
        }
    }
    if (!undumped_children.empty()) {
        os << padding << "... Non-layout children of "
           << getWidgetDescriptor(w) << ":\n";
        foreach (QWidget* child, undumped_children) {
            dumped_children.append(
                dumpWidgetAndChildren(os, child, level + 1, "", config));
        }
    }
    return dumped_children;
}


void dumpWidgetHierarchy(const QWidget* w, const DumperConfig& config)
{
    QDebug os = qDebug().noquote().nospace();
    os << "WIDGET HIERARCHY:\n";
    dumpWidgetAndChildren(os, w, 0, "", config);
}


}  // namespace layoutdumper