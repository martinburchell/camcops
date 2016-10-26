/*===========================================================================
==
== Copyright (C) 2016 The Qt Company Ltd.
== Contact: https://www.qt.io/licensing/
==
== This file is part of the examples of the Qt Toolkit.
==
== $QT_BEGIN_LICENSE:BSD$
== Commercial License Usage
== Licensees holding valid commercial Qt licenses may use this file in
== accordance with the commercial license agreement provided with the
== Software or, alternatively, in accordance with the terms contained in
== a written agreement between you and The Qt Company. For licensing terms
== and conditions see https://www.qt.io/terms-conditions. For further
== information use the contact form at https://www.qt.io/contact-us.
==
== BSD License Usage
== Alternatively, you may use this file under the terms of the BSD license
== as follows:
==
== "Redistribution and use in source and binary forms, with or without
== modification, are permitted provided that the following conditions are
== met:
==   * Redistributions of source code must retain the above copyright
==     notice, this list of conditions and the following disclaimer.
==   * Redistributions in binary form must reproduce the above copyright
==     notice, this list of conditions and the following disclaimer in
==     the documentation and/or other materials provided with the
==     distribution.
==   * Neither the name of The Qt Company Ltd nor the names of its
==     contributors may be used to endorse or promote products derived
==     from this software without specific prior written permission.
==
==
== THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
== "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
== LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
== A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
== OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
== SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
== LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
== DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
== THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
== (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
== OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
==
== $QT_END_LICENSE$
==
===========================================================================*/

// #define DEBUG_LAYOUT

#ifdef DEBUG_LAYOUT
#include <QDebug>  // RNC
#include "lib/layoutdumper.h"
#endif
#include <QtWidgets>

#include "flowlayout.h"


FlowLayout::FlowLayout(QWidget* parent, int margin,
                       int h_spacing, int v_spacing) :
    QLayout(parent),
    m_h_space(h_spacing),
    m_v_space(v_spacing)
{
    commonConstructor(margin);
}


FlowLayout::FlowLayout(int margin, int h_spacing, int v_spacing) :
    m_h_space(h_spacing),
    m_v_space(v_spacing)
{
    commonConstructor(margin);
}


void FlowLayout::commonConstructor(int margin)
{
    setContentsMargins(margin, margin, margin, margin);
}


FlowLayout::~FlowLayout()
{
    // RNC: crash here relating to double deletion.
    // - From http://doc.qt.io/qt-4.8/layout.html :
    //   "Note: Widgets in a layout are children of the widget on which the
    //   layout is installed, not of the layout itself. Widgets can only have
    //   other widgets as parent, not layouts."
    // - Note from qwidget.cpp that QWidget::~QWidget() deletes its children.
    // - However, from
    //   http://doc.qt.io/qt-5/qtwidgets-layouts-flowlayout-example.html
    //   ... "When using addItem() the ownership of the layout items is
    //   transferred to the layout, and it is therefore the layout's
    //   responsibility to delete them."
    // - In other word, the layout owns the QLayoutItem objects; the layout's
    //   parent widget owns the child widgets.
    QLayoutItem* item;
    while ((item = takeAt(0))) {
#ifdef DEBUG_LAYOUT
        qDebug().noquote() << "delete QLayoutItem"
                           << LayoutDumper::toString(item);
#endif
        delete item;
#ifdef DEBUG_LAYOUT
        qDebug() << "... deleted";
#endif
    }
}


void FlowLayout::addItem(QLayoutItem* item)
{
    m_item_list.append(item);
    invalidate();
}


int FlowLayout::horizontalSpacing() const
{
    if (m_h_space >= 0) {
        return m_h_space;
    } else {
        return smartSpacing(QStyle::PM_LayoutHorizontalSpacing);
    }
}


int FlowLayout::verticalSpacing() const
{
    if (m_v_space >= 0) {
        return m_v_space;
    } else {
        return smartSpacing(QStyle::PM_LayoutVerticalSpacing);
    }
}


int FlowLayout::count() const
{
    return m_item_list.size();
}


QLayoutItem* FlowLayout::itemAt(int index) const
{
    return m_item_list.value(index);
}


QLayoutItem* FlowLayout::takeAt(int index)
{
    if (index >= 0 && index < m_item_list.size()) {
        return m_item_list.takeAt(index);
        // http://doc.qt.io/qt-5/qlist.html#takeAt
    } else {
        return nullptr;
    }
}


Qt::Orientations FlowLayout::expandingDirections() const
{
    // http://doc.qt.io/qt-5/qlayout.html#expandingDirections
    return 0;
}


bool FlowLayout::hasHeightForWidth() const
{
    return true;
}


int FlowLayout::heightForWidth(int width) const
{
    if (!m_width_to_height.contains(width)) {
#ifdef DEBUG_LAYOUT
        qDebug() << Q_FUNC_INFO << "- CALCULATING";
#endif
        QSize size = doLayout(QRect(0, 0, width, 0), true);
        m_width_to_height[width] = size.height();
    } else {
#ifdef DEBUG_LAYOUT
        qDebug() << Q_FUNC_INFO << "- using cached";
#endif
    }
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << "... width" << width
             << "-> height" << m_width_to_height[width];
#endif
    return m_width_to_height[width];
}


void FlowLayout::setGeometry(const QRect& rect)
{
    // This is the master entry point for actually laying out the layout's
    // member widgets.
    QLayout::setGeometry(rect);
    doLayout(rect, false);
}


QSize FlowLayout::sizeHint() const
{
    // Hint is based on an area as wide as we could possibly want.
    if (!m_size_hint.isValid()) {
#ifdef DEBUG_LAYOUT
        qDebug() << Q_FUNC_INFO << "- CALCULATING";
#endif
        m_size_hint = doLayout(QRect(0, 0, QWIDGETSIZE_MAX, 0), true);
    } else {
#ifdef DEBUG_LAYOUT
        qDebug() << Q_FUNC_INFO << "- using cached";
#endif
    }
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO << "->" << m_size_hint;
#endif
    return m_size_hint;
}


void FlowLayout::invalidate()
{
    m_size_hint = QSize();
    m_width_to_height.clear();
}


QSize FlowLayout::minimumSize() const
{
    // Not sure this is right.
    // Though also: not sure it's vital, with heightForWidth().
    // Certainly seems to work OK now small off-by-one arithmetic errors fixed
    // in doLayout.
    QSize size;
    QLayoutItem* item;
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
#endif
    foreach (item, m_item_list) {
        QSize item_minimum_size = item->minimumSize();
        size = size.expandedTo(item_minimum_size);
#ifdef DEBUG_LAYOUT
        qDebug().nospace() << "... item minimum " << item_minimum_size
                           << "; size now " << size;
#endif
    }
    // ... the minimum size of the largest single child widget

    size += QSize(2 * margin(), 2 * margin());
#ifdef DEBUG_LAYOUT
    qDebug() << "... returning" << size;
#endif
    return size;
}


QSize FlowLayout::doLayout(const QRect& rect, bool test_only) const
{
    int left, top, right, bottom;
    getContentsMargins(&left, &top, &right, &bottom);
    QRect effective_rect = rect.adjusted(+left, +top, -right, -bottom);
    const int layout_width = effective_rect.width();
#ifdef DEBUG_LAYOUT
    qDebug() << Q_FUNC_INFO;
    qDebug() << "... test_only =" << test_only;
    qDebug() << "... layout_width =" << layout_width;
#endif
    int x = effective_rect.x();
    int max_x = x;
    int y = effective_rect.y();
    int line_height = 0;

    QLayoutItem* item;
    foreach (item, m_item_list) {
        QWidget* wid = item->widget();
        int space_x = horizontalSpacing();
        if (space_x == -1) {
            space_x = wid->style()->layoutSpacing(
                QSizePolicy::PushButton, QSizePolicy::PushButton, Qt::Horizontal);
        }
        int space_y = verticalSpacing();
        if (space_y == -1) {
            space_y = wid->style()->layoutSpacing(
                QSizePolicy::PushButton, QSizePolicy::PushButton, Qt::Vertical);
        }

        // RNC: modified here to handle height-for-width items, and deal with
        // a layout width smaller than the widget's preferred (but bigger than
        // their minimum).
        int available_width = effective_rect.right() - x + 1;
        // http://doc.qt.io/qt-5/qrect.html#details

        QSize item_size_hint = item->sizeHint();
        int item_width = item_size_hint.width();  // item's preferred width

#ifdef DEBUG_LAYOUT
        qDebug().nospace() << "... y " << y
                           << ", x " << x
                           << ", available_width " << available_width
                           << ", item_width " << item_width;
#endif

        bool start_new_line = false;
        if (available_width < item_width) {
            int relative_x = x - effective_rect.x();
            if (relative_x > 0) {
                start_new_line = true;
                item_width = qMin(item_width, layout_width);
#ifdef DEBUG_LAYOUT
                qDebug() << "... start new line; item_width now" << item_width;
#endif
            } else {
                // Already at the start of a row; we have to make do.
                // Shrink the item.
                item_width = available_width;
                // Should be at least item->minimumSize().width(), by the
                // bottom-up (widget -> parent) constraints.
#ifdef DEBUG_LAYOUT
                qDebug() << "... alter item_width to" << item_width;
#endif
            }
        }

        if (start_new_line) {
            // Overflowing to the right; start a new line.
            // Original Qt version also had "&& line_height > 0"; not sure
            // that helps.
            x = effective_rect.x();
            y = y + line_height + space_y;
            line_height = 0;
        }

        int item_height = item->hasHeightForWidth()
                ? item->heightForWidth(item_width)
                : item_size_hint.height();
        max_x = qMax(max_x, x + item_width);

        if (!test_only) {
            item->setGeometry(QRect(QPoint(x, y),
                                    QSize(item_width, item_height)));
        }

        int next_x = x + item_width + space_x;
        x = next_x;
        line_height = qMax(line_height, item_height);
    }

    int final_width = max_x - rect.x();
    int final_height = y + line_height - rect.y() + bottom;
    QSize final_size(final_width, final_height);
#ifdef DEBUG_LAYOUT
    qDebug() << "... LAYOUT COMPLETE; final size" << final_size;
#endif
    return final_size;
    // Original Qt version returned height only.
}


int FlowLayout::smartSpacing(QStyle::PixelMetric pm) const
{
    QObject* parent = this->parent();
    if (!parent) {
        return -1;
    } else if (parent->isWidgetType()) {
        QWidget* pw = static_cast<QWidget*>(parent);
        return pw->style()->pixelMetric(pm, 0, pw);
    } else {
        return static_cast<QLayout*>(parent)->spacing();
    }
}
