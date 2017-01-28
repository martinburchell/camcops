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

// http://stackoverflow.com/questions/5653114/display-image-in-qt-to-fit-label-size
// http://stackoverflow.com/questions/8211982/qt-resizing-a-qlabel-containing-a-qpixmap-while-keeping-its-aspect-ratio
// ... hacked around a bit, because it wasn't using more size when offered
// http://stackoverflow.com/questions/24264320/qt-layouts-keep-widget-aspect-ratio-while-resizing/24264774

// Eventually this:
// http://stackoverflow.com/questions/452333/how-to-maintain-widgets-aspect-ratio-in-qt
// https://forum.qt.io/topic/29859/solved-trying-to-fix-aspect-ratio-of-a-widget-big-problems-with-layouts/5

// Consensus that setHeightForWidth doesn't work terribly well...

#include <QLabel>
#include <QPixmap>
class QMouseEvent;
class QResizeEvent;


class AspectRatioPixmapLabel : public QLabel
{
    // Image that retains its aspect ratio, for displaying photos.
    // - Displays image UP TO its original size.
    // - Clickable, in a simple way (as per https://wiki.qt.io/Clickable_QLabel)
    //   - this form of clicking responds immediately, not as you release the
    //   mouse click (cf. QAbstractButton); however, there is no visual display
    //   that responds to the start of the click, so maybe that is reasonable.
    //   For another way of responding to clicks, see ClickableLabel.

    Q_OBJECT
public:
    explicit AspectRatioPixmapLabel(QWidget* parent = nullptr);
    virtual int heightForWidth(int width) const override;
    virtual QSize sizeHint() const override;
    virtual QSize minimumSizeHint() const override;
    QPixmap scaledPixmap() const;
    void clear();
protected:
    virtual void mousePressEvent(QMouseEvent* event) override;
signals:
    void clicked();
public slots:
    virtual void setPixmap(const QPixmap& pixmap);  // WON'T OVERRIDE.
    // - SO QLabel PROPERTY ACCESSORS ARE NOT VIRTUAL.
    // - AND YOU MUST BEWARE WHAT POINTER TYPE YOU ACCESS THIS THROUGH!
    virtual void resizeEvent(QResizeEvent* event) override;
private:
    QPixmap m_pixmap;
};