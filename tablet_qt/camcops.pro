#-------------------------------------------------
#
# Project created by QtCreator 2016-05-30T22:51:39
#
#-------------------------------------------------

# http://doc.qt.io/qt-5.7/qmake-project-files.html
# http://doc.qt.io/qt-5.7/qmake-variable-reference.html

# =============================================================================
# Prerequisites: environment variables
# =============================================================================
# Need environment variable CAMCOPS_QT_BASE_DIR
# Put something like this in your ~/.profile:
#   export CAMCOPS_QT_BASE_DIR="/home/rudolf/dev/qt_local_build"

# This file is read by qmake.
# Use $$(...) to read an environment variable at the time of qmake.
# Use $(...) to read an environment variable at the time of make.
# Use $$... or $${...} to read a Qt project file variable.
# See
# - http://doc.qt.io/qt-4.8/qmake-advanced-usage.html#variables
# - http://doc.qt.io/qt-5/qmake-test-function-reference.html
# Here, we copy an environment variable to a Qt project file variable:
QT_BASE_DIR = $(CAMCOPS_QT_BASE_DIR)  # value at time of make
QT_BASE_DIR_AT_QMAKE = $$(CAMCOPS_QT_BASE_DIR)  # value at time of qmake ("now")
message("Using base directory: '$${QT_BASE_DIR_AT_QMAKE}'")
isEmpty(QT_BASE_DIR_AT_QMAKE) {
    error("Environment variable CAMCOPS_QT_BASE_DIR is undefined")
}

# =============================================================================
# Parts of Qt
# =============================================================================

# SQLite/Android and OpenSSL/anything requires a custom Qt build.
# ALSO TRY:
#   qmake -query  # for the qmake of the Qt build you're using

# http://doc.qt.io/qt-5/qtmultimedia-index.html
# http://wiki.qt.io/Qt_5.5.0_Multimedia_Backends
# http://doc.qt.io/qt-4.8/qmake-variable-reference.html#qt
# http://doc.qt.io/qt-5/qtmodules.html

QT += core  # included by default; QtCore module
QT += gui  # included by default; QtGui module
QT += multimedia  # or: undefined reference to QMedia*::*
QT += multimediawidgets
QT += network  # required to #include <QtNetwork/*>
QT += sql  # required to #include <QSqlDatabase>
QT += svg  # required to #include <QGraphicsSvgItem> or <QSvgRenderer>
# QT += webkit  # for QWebView -- no, not used
# QT += webkitwidgets  # for QWebView -- no, not used
QT += widgets  # required to #include <QApplication>

# http://stackoverflow.com/questions/20351155/how-can-i-enable-ssl-in-qt-windows-application
# http://stackoverflow.com/questions/18663331/how-to-check-the-selected-version-of-qt-in-a-pro-file

# =============================================================================
# Overall configuration
# =============================================================================

CONFIG += static  # use a statically linked version of Qt
# CONFIG += debug  # no, use the QtCreator debug/release settings
CONFIG += mobility
CONFIG += c++11

# For SQLCipher (see its README.md):
# http://stackoverflow.com/questions/16244040/is-the-qt-defines-doing-the-same-thing-as-define-in-c
DEFINES += SQLITE_HAS_CODEC
DEFINES += SQLITE_TEMP_STORE=2

MOBILITY =

# PKGCONFIG += openssl
# ... http://stackoverflow.com/questions/14681012/how-to-include-openssl-in-a-qt-project
# ... but no effect? Not mentioned in variable reference (above).
LIBS += -lssl
# ... not working either? Doesn't complain, but ldd still shows that system libssl.so is in use

LIBS += "$$QT_BASE_DIR/src/sqlcipher/sqlite3.o"

# =============================================================================
# Compiler flags
# =============================================================================

QMAKE_CXXFLAGS += -Werror  # warnings become errors

# In release mode, optimize heavily:
QMAKE_CXXFLAGS_RELEASE -= -O
QMAKE_CXXFLAGS_RELEASE -= -O1
QMAKE_CXXFLAGS_RELEASE -= -O2
QMAKE_CXXFLAGS_RELEASE += -O3  # optimize heavily

# =============================================================================
# Build targets
# =============================================================================

TARGET = camcops
TEMPLATE = app

# =============================================================================
# Paths
# =============================================================================
# See build_qt.py for how these are built (or not built) as required.

INCLUDEPATH += "$$QT_BASE_DIR/eigen/eigen-eigen-67e894c6cd8f"  # from which: <Eigen/...>
# INCLUDEPATH += "$$QT_BASE_DIR/armadillo/armadillo-7.950.0/include"  # from which: <armadillo>
# INCLUDEPATH += "$$QT_BASE_DIR/armadillo/armadillo-7.950.0/include/armadillo_bits"
# INCLUDEPATH += "$$QT_BASE_DIR/boost/boost_1_64_0"  # from which: <boost/...>
# INCLUDEPATH += "$$QT_BASE_DIR/src/mlpack/src"  # from which: <mlpack/...>
INCLUDEPATH += "$$QT_BASE_DIR/openssl_linux_build/openssl-1.0.2h/include"  # *** nasty hard-coding
INCLUDEPATH += "$$QT_BASE_DIR/src"  # from which: <sqlcipher/sqlite3.h>

# =============================================================================
# Resources and source files
# =============================================================================

RESOURCES += \
    camcops.qrc

SOURCES += main.cpp \
    common/appstrings.cpp \
    common/camcopsapp.cpp \
    common/camcopsversion.cpp \
    common/cssconst.cpp \
    common/dbconstants.cpp \
    common/globals.cpp \
    common/platform.cpp \
    common/textconst.cpp \
    common/uiconst.cpp \
    common/varconst.cpp \
    common/version.cpp \
    common/widgetconst.cpp \
    crypto/cryptofunc.cpp \
    crypto/secureqbytearray.cpp \
    crypto/secureqstring.cpp \
    db/ancillaryfunc.cpp \
    db/databaseobject.cpp \
    db/dbfunc.cpp \
    db/dbnestabletransaction.cpp \
    db/dbtransaction.cpp \
    db/dumpsql.cpp \
    db/field.cpp \
    db/fieldcreationplan.cpp \
    db/fieldref.cpp \
    dbobjects/blob.cpp \
    dbobjects/extrastring.cpp \
    dbobjects/patient.cpp \
    dbobjects/patientsorter.cpp \
    dbobjects/storedvar.cpp \
    db/sqlargs.cpp \
    db/sqlcachedresult.cpp \
    db/sqlcipherdriver.cpp \
    db/sqlcipherhelpers.cpp \
    db/sqlcipherresult.cpp \
    db/sqlitepragmainfofield.cpp \
    db/whichdb.cpp \
    diagnosis/diagnosissortfiltermodel.cpp \
    diagnosis/diagnosticcode.cpp \
    diagnosis/diagnosticcodeset.cpp \
    diagnosis/flatproxymodel.cpp \
    diagnosis/icd10.cpp \
    diagnosis/icd9cm.cpp \
    dialogs/logbox.cpp \
    dialogs/logmessagebox.cpp \
    dialogs/nvpchoicedialog.cpp \
    dialogs/pagepickerdialog.cpp \
    dialogs/passwordchangedialog.cpp \
    dialogs/passwordentrydialog.cpp \
    dialogs/progressbox.cpp \
    dialogs/scrollmessagebox.cpp \
    dialogs/waitbox.cpp \
    lib/ccrandom.cpp \
    lib/containers.cpp \
    lib/convert.cpp \
    lib/css.cpp \
    lib/datetime.cpp \
    lib/debugfunc.cpp \
    lib/filefunc.cpp \
    lib/flagguard.cpp \
    lib/geometry.cpp \
    lib/graphicsfunc.cpp \
    lib/idpolicy.cpp \
    lib/imagefunc.cpp \
    lib/layoutdumper.cpp \
    lib/linesegment.cpp \
    maths/mathfunc.cpp \
    lib/networkmanager.cpp \
    lib/nhs.cpp \
    lib/numericfunc.cpp \
    lib/paintertranslaterotatecontext.cpp \
    lib/penbrush.cpp \
    lib/reentrydepthguard.cpp \
    lib/roman.cpp \
    lib/sizehelpers.cpp \
    lib/slowguiguard.cpp \
    lib/slownonguifunctioncaller.cpp \
    lib/stringfunc.cpp \
    lib/threadworker.cpp \
    lib/uifunc.cpp \
    menu/addictionmenu.cpp \
    menu/affectivemenu.cpp \
    menu/alltasksmenu.cpp \
    menu/anonymousmenu.cpp \
    menu/catatoniaepsemenu.cpp \
    menu/choosepatientmenu.cpp \
    menu/clinicalmenu.cpp \
    menu/clinicalsetsmenu.cpp \
    menu/cognitivemenu.cpp \
    menu/executivemenu.cpp \
    menu/globalmenu.cpp \
    menu/helpmenu.cpp \
    menulib/choosepatientmenuitem.cpp \
    menulib/htmlinfowindow.cpp \
    menulib/htmlmenuitem.cpp \
    menulib/menuheader.cpp \
    menulib/menuitem.cpp \
    menulib/menuwindow.cpp \
    menulib/taskmenuitem.cpp \
    menu/mainmenu.cpp \
    menu/patientsummarymenu.cpp \
    menu/personalitymenu.cpp \
    menu/psychosismenu.cpp \
    menu/researchmenu.cpp \
    menu/researchsetsmenu.cpp \
    menu/setmenucpftaffective1.cpp \
    menu/setmenudeakin1.cpp \
    menu/setmenufromlp.cpp \
    menu/setmenuobrien1.cpp \
    menu/settingsmenu.cpp \
    menu/singletaskmenu.cpp \
    menu/testmenu.cpp \
    menu/whiskermenu.cpp \
    menu/widgettestmenu.cpp \
    qobjects/comparers.cpp \
    qobjects/focuswatcher.cpp \
    qobjects/keypresswatcher.cpp \
    qobjects/shootabug.cpp \
    qobjects/showwatcher.cpp \
    qobjects/strictdoublevalidator.cpp \
    qobjects/strictint64validator.cpp \
    qobjects/strictintvalidator.cpp \
    qobjects/strictuint64validator.cpp \
    qobjects/stylenofocusrect.cpp \
    questionnairelib/commonoptions.cpp \
    questionnairelib/mcqfunc.cpp \
    questionnairelib/mcqgridsubtitle.cpp \
    questionnairelib/namevalueoptions.cpp \
    questionnairelib/namevaluepair.cpp \
    questionnairelib/pagepickeritem.cpp \
    questionnairelib/quaudioplayer.cpp \
    questionnairelib/quboolean.cpp \
    questionnairelib/qubutton.cpp \
    questionnairelib/qucanvas.cpp \
    questionnairelib/qucountdown.cpp \
    questionnairelib/qudatetime.cpp \
    questionnairelib/qudiagnosticcode.cpp \
    questionnairelib/quelement.cpp \
    questionnairelib/questionnaire.cpp \
    questionnairelib/questionnairefunc.cpp \
    questionnairelib/questionnaireheader.cpp \
    questionnairelib/questionwithonefield.cpp \
    questionnairelib/questionwithtwofields.cpp \
    questionnairelib/quflowcontainer.cpp \
    questionnairelib/qugridcell.cpp \
    questionnairelib/qugridcontainer.cpp \
    questionnairelib/quheading.cpp \
    questionnairelib/quhorizontalcontainer.cpp \
    questionnairelib/quhorizontalline.cpp \
    questionnairelib/quimage.cpp \
    questionnairelib/qulineedit.cpp \
    questionnairelib/qulineeditdouble.cpp \
    questionnairelib/qulineeditinteger.cpp \
    questionnairelib/qulineeditlonglong.cpp \
    questionnairelib/qulineeditulonglong.cpp \
    questionnairelib/qumcq.cpp \
    questionnairelib/qumcqgrid.cpp \
    questionnairelib/qumcqgriddouble.cpp \
    questionnairelib/qumcqgriddoublesignaller.cpp \
    questionnairelib/qumcqgridsignaller.cpp \
    questionnairelib/qumcqgridsingleboolean.cpp \
    questionnairelib/qumcqgridsinglebooleansignaller.cpp \
    questionnairelib/qumultipleresponse.cpp \
    questionnairelib/qupage.cpp \
    questionnairelib/quphoto.cpp \
    questionnairelib/qupickerinline.cpp \
    questionnairelib/qupickerpopup.cpp \
    questionnairelib/quslider.cpp \
    questionnairelib/quspacer.cpp \
    questionnairelib/quspinboxdouble.cpp \
    questionnairelib/quspinboxinteger.cpp \
    questionnairelib/qutext.cpp \
    questionnairelib/qutextedit.cpp \
    questionnairelib/quthermometer.cpp \
    questionnairelib/quthermometeritem.cpp \
    questionnairelib/quverticalcontainer.cpp \
    tasklib/inittasks.cpp \
    tasklib/task.cpp \
    tasklib/taskfactory.cpp \
    tasklib/taskproxy.cpp \
    tasklib/taskregistrar.cpp \
    tasklib/tasksorter.cpp \
    tasks/ace3.cpp \
    tasks/aims.cpp \
    tasks/auditc.cpp \
    tasks/audit.cpp \
    tasks/badls.cpp \
    tasks/bdi.cpp \
    tasks/bmi.cpp \
    tasks/bprs.cpp \
    tasks/bprse.cpp \
    tasks/cage.cpp \
    tasks/cape42.cpp \
    tasks/caps.cpp \
    tasks/cardinalexpdetthreshold.cpp \
    tasks/cbir.cpp \
    tasks/cecaq3.cpp \
    tasks/cgi.cpp \
    tasks/cgii.cpp \
    tasks/cgisch.cpp \
    tasks/cisr.cpp \
    tasks/ciwa.cpp \
    tasks/contactlog.cpp \
    tasks/copebrief.cpp \
    tasks/cpftlpsdischarge.cpp \
    tasks/cpftlpsreferral.cpp \
    tasks/cpftlpsresetresponseclock.cpp \
    tasks/dad.cpp \
    tasks/dast.cpp \
    tasks/deakin1healthreview.cpp \
    tasks/demoquestionnaire.cpp \
    tasks/demqol.cpp \
    tasks/demqolproxy.cpp \
    tasks/diagnosisicd10.cpp \
    tasks/diagnosisicd9cm.cpp \
    tasks/distressthermometer.cpp \
    tasks/fast.cpp \
    tasks/fft.cpp \
    tasks/frs.cpp \
    tasks/gad7.cpp \
    tasks/gaf.cpp \
    tasks/gds15.cpp \
    tasks/gmcpq.cpp \
    tasks/hads.cpp \
    tasks/hadsrespondent.cpp \
    tasks/hama.cpp \
    tasks/hamd7.cpp \
    tasks/hamd.cpp \
    tasks/honos65.cpp \
    tasks/honosca.cpp \
    tasks/honos.cpp \
    tasks/icd10depressive.cpp \
    tasks/icd10manic.cpp \
    tasks/icd10mixed.cpp \
    tasks/icd10schizophrenia.cpp \
    tasks/icd10schizotypal.cpp \
    tasks/icd10specpd.cpp \
    tasks/ided3d.cpp \
    tasks/iesr.cpp \
    tasks/ifs.cpp \
    tasks/irac.cpp \
    tasks/mast.cpp \
    tasks/mdsupdrs.cpp \
    tasks/moca.cpp \
    tasks/nart.cpp \
    tasks/npiq.cpp \
    tasks/panss.cpp \
    tasks/patientsatisfaction.cpp \
    tasks/pclc.cpp \
    tasks/pclm.cpp \
    tasks/pcls.cpp \
    tasks/pdss.cpp \
    tasks/photo.cpp \
    tasks/photosequence.cpp \
    tasks/phq15.cpp \
    tasks/phq9.cpp \
    tasks/progressnote.cpp \
    tasks/pswq.cpp \
    tasks/psychiatricclerking.cpp \
    tasks/qolbasic.cpp \
    tasks/qolsg.cpp \
    tasks/rand36.cpp \
    tasks/referrersatisfactiongen.cpp \
    tasks/referrersatisfactionspec.cpp \
    tasks/slums.cpp \
    tasks/smast.cpp \
    tasks/swemwbs.cpp \
    tasks/wemwbs.cpp \
    tasks/wsas.cpp \
    tasks/ybocs.cpp \
    tasks/ybocssc.cpp \
    tasks/zbi12.cpp \
    taskxtra/diagnosisicd10item.cpp \
    taskxtra/diagnosisicd9cmitem.cpp \
    taskxtra/diagnosisitembase.cpp \
    taskxtra/diagnosistaskbase.cpp \
    taskxtra/ided3dexemplars.cpp \
    taskxtra/ided3dstage.cpp \
    taskxtra/ided3dtrial.cpp \
    taskxtra/pclcommon.cpp \
    taskxtra/photosequencephoto.cpp \
    taskxtra/satisfactioncommon.cpp \
    widgets/adjustablepie.cpp \
    widgets/aspectratiopixmap.cpp \
    widgets/basewidget.cpp \
    widgets/booleanwidget.cpp \
    widgets/boxlayouthfw.cpp \
    widgets/camera.cpp \
    widgets/canvaswidget.cpp \
    widgets/clickablelabelnowrap.cpp \
    widgets/clickablelabelwordwrapwide.cpp \
    widgets/diagnosticcodeselector.cpp \
    widgets/fixedareahfwtestwidget.cpp \
    widgets/flickcharm.cpp \
    widgets/flowlayouthfw.cpp \
    widgets/graphicsrectitemclickable.cpp \
    widgets/gridlayouthfw.cpp \
    widgets/growingtextedit.cpp \
    widgets/hboxlayouthfw.cpp \
    widgets/heightforwidthlistwidget.cpp \
    widgets/horizontalline.cpp \
    widgets/imagebutton.cpp \
    widgets/labelwordwrapwide.cpp \
    widgets/margins.cpp \
    widgets/openablewidget.cpp \
    widgets/qtlayouthelpers.cpp \
    widgets/screenlikegraphicsview.cpp \
    widgets/spacer.cpp \
    widgets/svgwidgetclickable.cpp \
    widgets/tickslider.cpp \
    widgets/vboxlayouthfw.cpp \
    widgets/verticalline.cpp \
    widgets/verticalscrollarea.cpp \
    widgets/verticalscrollareaviewport.cpp \
    tasks/cardinalexpectationdetection.cpp \
    dialogs/soundtestdialog.cpp \
    taskxtra/cardinalexpdetcommon.cpp \
    taskxtra/cardinalexpdetthresholdtrial.cpp \
    maths/mlpackfunc.cpp \
    maths/eigenfunc.cpp \
    maths/glm.cpp \
    maths/logisticregression.cpp \
    maths/linkfunctionfamily.cpp \
    maths/statsfunc.cpp

HEADERS += \
    common/aliases_camcops.h \
    common/aliases_qt.h \
    common/appstrings.h \
    common/camcopsapp.h \
    common/camcopsversion.h \
    common/cssconst.h \
    common/dbconstants.h \
    common/globals.h \
    common/gui_defines.h \
    common/layouts.h \
    common/platform.h \
    common/textconst.h \
    common/uiconst.h \
    common/varconst.h \
    common/version.h \
    common/widgetconst.h \
    crypto/cryptofunc.h \
    crypto/secureqbytearray.h \
    crypto/secureqstring.h \
    crypto/zallocator.h \
    db/ancillaryfunc.h \
    db/databaseobject.h \
    db/dbfunc.h \
    db/dbnestabletransaction.h \
    db/dbtransaction.h \
    db/dumpsql.h \
    db/fieldcreationplan.h \
    db/field.h \
    db/fieldref.h \
    dbobjects/blob.h \
    dbobjects/extrastring.h \
    dbobjects/patient.h \
    dbobjects/patientsorter.h \
    dbobjects/storedvar.h \
    db/sqlargs.h \
    db/sqlcachedresult.h \
    db/sqlcipherdriver.h \
    db/sqlcipherhelpers.h \
    db/sqlcipherresult.h \
    db/sqlitepragmainfofield.h \
    db/whichdb.h \
    diagnosis/diagnosissortfiltermodel.h \
    diagnosis/diagnosticcode.h \
    diagnosis/diagnosticcodeset.h \
    diagnosis/flatproxymodel.h \
    diagnosis/icd10.h \
    diagnosis/icd9cm.h \
    dialogs/logbox.h \
    dialogs/logmessagebox.h \
    dialogs/nvpchoicedialog.h \
    dialogs/pagepickerdialog.h \
    dialogs/passwordchangedialog.h \
    dialogs/passwordentrydialog.h \
    dialogs/progressbox.h \
    dialogs/scrollmessagebox.h \
    dialogs/waitbox.h \
    lib/ccrandom.h \
    lib/cloneable.h \
    lib/containers.h \
    lib/convert.h \
    lib/css.h \
    lib/datetime.h \
    lib/debugfunc.h \
    lib/filefunc.h \
    lib/flagguard.h \
    lib/geometry.h \
    lib/graphicsfunc.h \
    lib/idpolicy.h \
    lib/imagefunc.h \
    lib/layoutdumper.h \
    lib/linesegment.h \
    maths/mathfunc.h \
    lib/networkmanager.h \
    lib/nhs.h \
    lib/numericfunc.h \
    lib/paintertranslaterotatecontext.h \
    lib/penbrush.h \
    lib/reentrydepthguard.h \
    lib/roman.h \
    lib/sizehelpers.h \
    lib/slowguiguard.h \
    lib/slownonguifunctioncaller.h \
    lib/stringfunc.h \
    lib/threadworker.h \
    lib/uifunc.h \
    menu/addictionmenu.h \
    menu/affectivemenu.h \
    menu/alltasksmenu.h \
    menu/anonymousmenu.h \
    menu/catatoniaepsemenu.h \
    menu/choosepatientmenu.h \
    menu/clinicalmenu.h \
    menu/clinicalsetsmenu.h \
    menu/cognitivemenu.h \
    menu/executivemenu.h \
    menu/globalmenu.h \
    menu/helpmenu.h \
    menulib/choosepatientmenuitem.h \
    menulib/htmlinfowindow.h \
    menulib/htmlmenuitem.h \
    menulib/menuheader.h \
    menulib/menuitem.h \
    menulib/menuproxy.h \
    menulib/menuwindow.h \
    menulib/taskmenuitem.h \
    menu/mainmenu.h \
    menu/patientsummarymenu.h \
    menu/personalitymenu.h \
    menu/psychosismenu.h \
    menu/researchmenu.h \
    menu/researchsetsmenu.h \
    menu/setmenucpftaffective1.h \
    menu/setmenudeakin1.h \
    menu/setmenufromlp.h \
    menu/setmenuobrien1.h \
    menu/settingsmenu.h \
    menu/singletaskmenu.h \
    menu/testmenu.h \
    menu/whiskermenu.h \
    menu/widgettestmenu.h \
    qobjects/comparers.h \
    qobjects/focuswatcher.h \
    qobjects/keypresswatcher.h \
    qobjects/shootabug.h \
    qobjects/showwatcher.h \
    qobjects/strictdoublevalidator.h \
    qobjects/strictint64validator.h \
    qobjects/strictintvalidator.h \
    qobjects/strictuint64validator.h \
    qobjects/stylenofocusrect.h \
    questionnairelib/commonoptions.h \
    questionnairelib/mcqfunc.h \
    questionnairelib/mcqgridsubtitle.h \
    questionnairelib/namevalueoptions.h \
    questionnairelib/namevaluepair.h \
    questionnairelib/pagepickeritem.h \
    questionnairelib/quaudioplayer.h \
    questionnairelib/quboolean.h \
    questionnairelib/qubutton.h \
    questionnairelib/qucanvas.h \
    questionnairelib/qucountdown.h \
    questionnairelib/qudatetime.h \
    questionnairelib/qudiagnosticcode.h \
    questionnairelib/quelement.h \
    questionnairelib/questionnairefunc.h \
    questionnairelib/questionnaire.h \
    questionnairelib/questionnaireheader.h \
    questionnairelib/questionwithonefield.h \
    questionnairelib/questionwithtwofields.h \
    questionnairelib/quflowcontainer.h \
    questionnairelib/qugridcell.h \
    questionnairelib/qugridcontainer.h \
    questionnairelib/quheading.h \
    questionnairelib/quhorizontalcontainer.h \
    questionnairelib/quhorizontalline.h \
    questionnairelib/quimage.h \
    questionnairelib/qulineeditdouble.h \
    questionnairelib/qulineedit.h \
    questionnairelib/qulineeditinteger.h \
    questionnairelib/qulineeditlonglong.h \
    questionnairelib/qulineeditulonglong.h \
    questionnairelib/qumcqgriddouble.h \
    questionnairelib/qumcqgriddoublesignaller.h \
    questionnairelib/qumcqgrid.h \
    questionnairelib/qumcqgridsignaller.h \
    questionnairelib/qumcqgridsingleboolean.h \
    questionnairelib/qumcqgridsinglebooleansignaller.h \
    questionnairelib/qumcq.h \
    questionnairelib/qumultipleresponse.h \
    questionnairelib/qupage.h \
    questionnairelib/quphoto.h \
    questionnairelib/qupickerinline.h \
    questionnairelib/qupickerpopup.h \
    questionnairelib/quslider.h \
    questionnairelib/quspacer.h \
    questionnairelib/quspinboxdouble.h \
    questionnairelib/quspinboxinteger.h \
    questionnairelib/qutextedit.h \
    questionnairelib/qutext.h \
    questionnairelib/quthermometer.h \
    questionnairelib/quthermometeritem.h \
    questionnairelib/quverticalcontainer.h \
    tasklib/inittasks.h \
    tasklib/taskfactory.h \
    tasklib/task.h \
    tasklib/taskproxy.h \
    tasklib/taskregistrar.h \
    tasklib/tasksorter.h \
    tasks/ace3.h \
    tasks/aims.h \
    tasks/auditc.h \
    tasks/audit.h \
    tasks/badls.h \
    tasks/bdi.h \
    tasks/bmi.h \
    tasks/bprse.h \
    tasks/bprs.h \
    tasks/cage.h \
    tasks/cape42.h \
    tasks/caps.h \
    tasks/cardinalexpdetthreshold.h \
    tasks/cbir.h \
    tasks/cecaq3.h \
    tasks/cgi.h \
    tasks/cgii.h \
    tasks/cgisch.h \
    tasks/cisr.h \
    tasks/ciwa.h \
    tasks/contactlog.h \
    tasks/copebrief.h \
    tasks/cpftlpsdischarge.h \
    tasks/cpftlpsreferral.h \
    tasks/cpftlpsresetresponseclock.h \
    tasks/dad.h \
    tasks/dast.h \
    tasks/deakin1healthreview.h \
    tasks/demoquestionnaire.h \
    tasks/demqol.h \
    tasks/demqolproxy.h \
    tasks/diagnosisicd10.h \
    tasks/diagnosisicd9cm.h \
    tasks/distressthermometer.h \
    tasks/fast.h \
    tasks/fft.h \
    tasks/frs.h \
    tasks/gad7.h \
    tasks/gaf.h \
    tasks/gds15.h \
    tasks/gmcpq.h \
    tasks/hads.h \
    tasks/hadsrespondent.h \
    tasks/hama.h \
    tasks/hamd7.h \
    tasks/hamd.h \
    tasks/honos65.h \
    tasks/honosca.h \
    tasks/honos.h \
    tasks/icd10depressive.h \
    tasks/icd10manic.h \
    tasks/icd10mixed.h \
    tasks/icd10schizophrenia.h \
    tasks/icd10schizotypal.h \
    tasks/icd10specpd.h \
    tasks/ided3d.h \
    tasks/iesr.h \
    tasks/ifs.h \
    tasks/irac.h \
    tasks/mast.h \
    tasks/mdsupdrs.h \
    tasks/moca.h \
    tasks/nart.h \
    tasks/npiq.h \
    tasks/panss.h \
    tasks/patientsatisfaction.h \
    tasks/pclc.h \
    tasks/pclm.h \
    tasks/pcls.h \
    tasks/pdss.h \
    tasks/photo.h \
    tasks/photosequence.h \
    tasks/phq15.h \
    tasks/phq9.h \
    tasks/progressnote.h \
    tasks/pswq.h \
    tasks/psychiatricclerking.h \
    tasks/qolbasic.h \
    tasks/qolsg.h \
    tasks/rand36.h \
    tasks/referrersatisfactiongen.h \
    tasks/referrersatisfactionspec.h \
    tasks/slums.h \
    tasks/smast.h \
    tasks/swemwbs.h \
    tasks/wemwbs.h \
    tasks/wsas.h \
    tasks/ybocs.h \
    tasks/ybocssc.h \
    tasks/zbi12.h \
    taskxtra/diagnosisicd10item.h \
    taskxtra/diagnosisicd9cmitem.h \
    taskxtra/diagnosisitembase.h \
    taskxtra/diagnosistaskbase.h \
    taskxtra/ided3dexemplars.h \
    taskxtra/ided3dstage.h \
    taskxtra/ided3dtrial.h \
    taskxtra/pclcommon.h \
    taskxtra/photosequencephoto.h \
    taskxtra/satisfactioncommon.h \
    widgets/adjustablepie.h \
    widgets/aspectratiopixmap.h \
    widgets/basewidget.h \
    widgets/booleanwidget.h \
    widgets/boxlayouthfw.h \
    widgets/camera.h \
    widgets/canvaswidget.h \
    widgets/clickablelabelnowrap.h \
    widgets/clickablelabelwordwrapwide.h \
    widgets/diagnosticcodeselector.h \
    widgets/fixedareahfwtestwidget.h \
    widgets/flickcharm.h \
    widgets/flowlayouthfw.h \
    widgets/graphicsrectitemclickable.h \
    widgets/gridlayouthfw.h \
    widgets/growingtextedit.h \
    widgets/hboxlayouthfw.h \
    widgets/heightforwidthlistwidget.h \
    widgets/horizontalline.h \
    widgets/imagebutton.h \
    widgets/labelwordwrapwide.h \
    widgets/margins.h \
    widgets/openablewidget.h \
    widgets/qtlayouthelpers.h \
    widgets/screenlikegraphicsview.h \
    widgets/spacer.h \
    widgets/svgwidgetclickable.h \
    widgets/tickslider.h \
    widgets/vboxlayouthfw.h \
    widgets/verticalline.h \
    widgets/verticalscrollarea.h \
    widgets/verticalscrollareaviewport.h \
    tasks/cardinalexpectationdetection.h \
    dialogs/soundtestdialog.h \
    taskxtra/cardinalexpdetcommon.h \
    taskxtra/cardinalexpdetthresholdtrial.h \
    maths/mlpackfunc.h \
    maths/eigenfunc.h \
    maths/glm.h \
    maths/logisticregression.h \
    maths/linkfunctionfamily.h \
    maths/statsfunc.h

DISTFILES += \
    android/AndroidManifest.xml \
    android/build.gradle \
    android/gradlew \
    android/gradlew.bat \
    android/gradle/wrapper/gradle-wrapper.jar \
    android/gradle/wrapper/gradle-wrapper.properties \
    android/res/drawable-ldpi/icon.png \
    android/res/values/libs.xml \
    images/dt/dt_sel_0.png \
    images/dt/dt_sel_10.png \
    images/dt/dt_sel_1.png \
    images/dt/dt_sel_2.png \
    images/dt/dt_sel_3.png \
    images/dt/dt_sel_4.png \
    images/dt/dt_sel_5.png \
    images/dt/dt_sel_6.png \
    images/dt/dt_sel_7.png \
    images/dt/dt_sel_8.png \
    images/dt/dt_sel_9.png \
    images/dt/dt_unsel_0.png \
    images/dt/dt_unsel_10.png \
    images/dt/dt_unsel_1.png \
    images/dt/dt_unsel_2.png \
    images/dt/dt_unsel_3.png \
    images/dt/dt_unsel_4.png \
    images/dt/dt_unsel_5.png \
    images/dt/dt_unsel_6.png \
    images/dt/dt_unsel_7.png \
    images/dt/dt_unsel_8.png \
    images/dt/dt_unsel_9.png \
    LICENSE.txt \
    notes/coding_conventions.txt \
    notes/known_problems.txt \
    notes/layout_notes.txt \
    notes/overall_design.txt \
    notes/qt_notes.txt \
    notes/rejected_ideas.txt \
    notes/string_formats.txt \
    notes/to_do.txt \
    stylesheets/camcops.css \
    stylesheets/camcops_menu.css \
    stylesheets/camcops_questionnaire.css \
    stylesheets/camera.css \
    tools/build_qt.py \
    tools/chord.py \
    tools/cppclean_all.sh \
    tools/decrypt_sqlcipher.py


# =============================================================================
# Android-specific options
# =============================================================================

ANDROID_PACKAGE_SOURCE_DIR = $$PWD/android

#contains(ANDROID_TARGET_ARCH,x86) {
#    ANDROID_EXTRA_LIBS = \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_x86_build/openssl-1.0.2h/libcrypto.so \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_x86_build/openssl-1.0.2h/libssl.so
#}
#contains(ANDROID_TARGET_ARCH,armeabi-v7a) {
#    ANDROID_EXTRA_LIBS = \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_arm_build/openssl-1.0.2h/libcrypto.so \
#        $$PWD/../../../../dev/qt_local_build/openssl_android_arm_build/openssl-1.0.2h/libssl.so
#}
