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
#include <QDialog>

class CentredDialog : public QDialog
{
    // Dialogue that repositions itself sensibly on orientation change.
    //
    // Currently we cannot rely on Android and iOS to handle this:
    // https://bugreports.qt.io/browse/QTBUG-91363
    // https://bugreports.qt.io/browse/QTBUG-109127
    //
    // Inspired by the DialogPositioner class in:
    // https://github.com/f4exb/sdrangel/

    Q_OBJECT
public:
    CentredDialog(QWidget* parent = nullptr);
protected:
    void sizeToScreen();
    void centre();
    bool eventFilter(QObject *obj, QEvent *event) override;
private slots:
    void orientationChanged(Qt::ScreenOrientation orientation);
};
