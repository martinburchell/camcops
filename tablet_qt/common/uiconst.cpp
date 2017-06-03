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

#include "uiconst.h"
#include <QObject>  // for tr()

namespace uiconst {

// ============================================================================
// Sizes
// ============================================================================

const QSize ICONSIZE(48, 48);
const QSize SMALL_ICONSIZE(24, 24);
const int SPACE = 4;
const int BIGSPACE = 16;
const int MEDIUMSPACE = 8;
const int HEADER_HLINE_WIDTH = 1;
const int QUESTIONNAIRE_HLINE_WIDTH = 2;
const int MCQGRID_VLINE_WIDTH = 1;
const int MCQGRID_VSPACING = 5;
const int MCQGRID_HSPACING = 5;
const int DEFAULT_COLSPAN_Q = 1;
const int DEFAULT_COLSPAN_A = 2;

const QMargins NO_MARGINS(0, 0, 0, 0);

// ============================================================================
// Stylesheets
// ============================================================================

#define camcopsStylesheetFilename(filename) (":/resources/camcops/stylesheets/" filename)

const QString CSS_CAMCOPS_MAIN(camcopsStylesheetFilename("main.css"));
const QString CSS_CAMCOPS_MENU(camcopsStylesheetFilename("menu.css"));
const QString CSS_CAMCOPS_QUESTIONNAIRE(camcopsStylesheetFilename(
            "questionnaire.css"));
const QString CSS_CAMCOPS_CAMERA(camcopsStylesheetFilename("camera.css"));
const QString CSS_CAMCOPS_DIAGNOSTIC_CODE(
        camcopsStylesheetFilename("diagnostic_code.css"));

// ============================================================================
// Fonts, colours
// ============================================================================

const QString WARNING_COLOUR("red");

const QColor BLACK(0, 0, 0);  // default a=255
const QColor GREY_200(200, 200, 200);
const QColor WHITE(255, 255, 255);
const QColor TRANSPARENT(0, 0, 0, 0);  // a=0 means fully transparent

const QColor RED(255, 0, 0);
const QColor GREEN(0, 255, 0);
const QColor BLUE(0, 0, 255);

const QColor BUTTON_UNPRESSED_COLOUR(127, 127, 127, 100);
const QColor BUTTON_PRESSED_COLOUR(100, 100, 255, 200);
const QColor BUTTON_DISABLED_COLOUR(127, 127, 127, 200);
const qreal DISABLED_ICON_OPACITY = 0.5;

// ============================================================================
// Images
// ============================================================================

const QString ICON_ADDICTION("addiction.png");
const QString ICON_AFFECTIVE("affective.png");
const QString ICON_ALLTASKS("alltasks.png");
const QString ICON_ANONYMOUS("anonymous.png");
const QString ICON_CAMCOPS("camcops.png");
const QString ICON_CATATONIA("catatonia.png");
const QString ICON_CHAIN("chain.png");
const QString ICON_CHOOSE_PATIENT("choose_patient.png");
const QString ICON_CLINICAL("clinical.png");
const QString ICON_COGNITIVE("cognitive.png");
const QString ICON_EXECUTIVE("executive.png");
const QString ICON_FIELD_INCOMPLETE_MANDATORY("field_incomplete_mandatory.png");
const QString ICON_FIELD_INCOMPLETE_OPTIONAL("field_incomplete_optional.png");
const QString ICON_FIELD_PROBLEM("field_problem.png");
const QString ICON_GLOBAL("global.png");
const QString ICON_HASCHILD("hasChild.png");
const QString ICON_HASPARENT("hasParent.png");
const QString ICON_INFO("info.png");
const QString ICON_PATIENT_SUMMARY("patient_summary.png");
const QString ICON_PERSONALITY("personality.png");
const QString ICON_PSYCHOSIS("psychosis.png");
const QString ICON_READ_ONLY("read_only.png");
const QString ICON_RESEARCH("research.png");
const QString ICON_SETS_CLINICAL("sets_clinical.png");
const QString ICON_SETS_RESEARCH("sets_research.png");
const QString ICON_SETTINGS("settings.png");
const QString ICON_STOP("stop.png");
const QString ICON_UPLOAD("upload.png");
const QString ICON_WARNING("warning.png");
const QString ICON_WHISKER("whisker.png");

// Filename stems
const QString CBS_ADD("add.png");
const QString CBS_BACK("back.png");
const QString CBS_CAMERA("camera.png");
const QString CBS_CANCEL("cancel.png");
const QString CBS_CHOOSE_PAGE("choose_page.png");
const QString CBS_DELETE("delete.png");
const QString CBS_EDIT("edit.png");
const QString CBS_FAST_FORWARD("fast_forward.png");
const QString CBS_FINISH("finish.png");
const QString CBS_FINISHFLAG("finishflag.png");
const QString CBS_LOCKED("locked.png");
const QString CBS_NEXT("next.png");
const QString CBS_OK("ok.png");
const QString CBS_PRIVILEGED("privileged.png");
const QString CBS_RELOAD("reload.png");
const QString CBS_ROTATE_ANTICLOCKWISE("rotate_anticlockwise.png");
const QString CBS_ROTATE_CLOCKWISE("rotate_clockwise.png");
const QString CBS_SPEAKER("speaker.png");
const QString CBS_SPEAKER_PLAYING("speaker_playing.png");
const QString CBS_TIME_NOW("time_now.png");
const QString CBS_UNLOCKED("unlocked.png");
const QString CBS_ZOOM("zoom.png");

// ============================================================================
// Sounds
// ============================================================================

const int MIN_VOLUME = 0;
const int MAX_VOLUME = 100;

const QString DEMO_SOUND_URL("qrc:///resources/camcops/sounds/portal_still_alive.mp3");  // *** change; copyright
const QString DEMO_SOUND_URL_2("qrc:///resources/camcops/sounds/soundtest.wav");  // *** change; copyright
const QString SOUND_COUNTDOWN_FINISHED("qrc:///resources/camcops/sounds/countdown_finished.wav");

// ============================================================================
// Network
// ============================================================================

const int IP_PORT_MIN = 0;
const int IP_PORT_MAX = 65536;
const int NETWORK_TIMEOUT_MS_MIN = 100;
const int NETWORK_TIMEOUT_MS_MAX = 5 * 60 * 1000;

}  // namespace uiconst