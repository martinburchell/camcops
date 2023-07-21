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

#include <QtTest/QtTest>
#include <QPushButton>

#include "layouts/flowlayouthfw.h"


class TestFlowLayoutHfw: public QObject
{
    Q_OBJECT

private slots:
    void testMinimumSizeAddsMargins();
};



void TestFlowLayoutHfw::testMinimumSizeAddsMargins()
{
    auto layout = new FlowLayoutHfw();
    auto button = new QPushButton();

    layout->addWidget(button);

    const int margin = 8;

    layout->setMargin(margin);

    QCOMPARE(layout->minimumSize(), QSize(2*margin, 2*margin));
}

QTEST_MAIN(TestFlowLayoutHfw)

#include "testflowlayouthfw.moc"
