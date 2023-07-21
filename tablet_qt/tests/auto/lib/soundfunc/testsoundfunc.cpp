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
#include <QAudioOutput>
#include <QMediaPlayer>

#include "lib/soundfunc.h"

using namespace soundfunc;

class TestSoundfunc: public QObject
{
    Q_OBJECT

private slots:
    void testSetVolumePercentSetsVolumeOnAudioOutput();
    void testSetVolumeProportionSetsVolumeOnAudioOutput();
};


void TestSoundfunc::testSetVolumePercentSetsVolumeOnAudioOutput()
{
    QSharedPointer<QMediaPlayer> player;
    makeMediaPlayer(player);

    const int volume_in = 50;
    setVolume(player, volume_in);

    const int volume_out = player->volume();
    QCOMPARE(volume_out, 50);
}

void TestSoundfunc::testSetVolumeProportionSetsVolumeOnAudioOutput()
{
    QSharedPointer<QMediaPlayer> player;
    makeMediaPlayer(player);

    const double volume_in = 0.5;
    setVolume(player, volume_in);

    const int volume_out = player->volume();
    QCOMPARE(volume_out, 50);
}

QTEST_MAIN(TestSoundfunc)

#include "testsoundfunc.moc"
