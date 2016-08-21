#include "camcopsapp.h"
#include <QApplication>
#include <QDateTime>
#include <QDialog>
#include <QMainWindow>
#include <QPushButton>
#include <QSqlDatabase>
#include <QStackedWidget>
#include "common/uiconstants.h"
#include "lib/datetimefunc.h"
#include "lib/dbfunc.h"
#include "lib/filefunc.h"
#include "menu/mainmenu.h"
#include "tasklib/inittasks.h"
#include "questionnairelib/questionnaire.h"


CamcopsApp::CamcopsApp(int& argc, char *argv[]) :
    QApplication(argc, argv),
    m_p_task_factory(nullptr),
    m_lockstate(LockState::Locked),
    m_whisker_connected(false),
    m_p_main_window(nullptr),
    m_p_window_stack(nullptr),
    m_patient_id(NONEXISTENT_PK)
{
    QDateTime dt = now();
    qInfo() << "CamCOPS starting at:" << qUtf8Printable(datetimeToIsoMs(dt))
            << "=" << qUtf8Printable(datetimeToIsoMsUtc(dt));

    // However, we can't do things like opening the database until we have
    // created the app. So don't open the database in the initializer list!

    // Database lifetime:
    // http://stackoverflow.com/questions/7669987/what-is-the-correct-way-of-qsqldatabase-qsqlquery
    m_db = QSqlDatabase::addDatabase("QSQLITE", "data");
    m_sysdb = QSqlDatabase::addDatabase("QSQLITE", "sys");
    openDatabaseOrDie(m_db, DATA_DATABASE_FILENAME);
    openDatabaseOrDie(m_sysdb, SYSTEM_DATABASE_FILENAME);

    m_p_task_factory = TaskFactoryPtr(new TaskFactory(*this));
    InitTasks(*m_p_task_factory);  // ensures all tasks are registered
    m_p_task_factory->finishRegistration();
    qInfo() << "Registered tasks:" << m_p_task_factory->tablenames();

    m_p_task_factory->makeAllTables();
    // *** also need to make the special tables at this point

    setStyleSheet(textfileContents(CSS_CAMCOPS));
}


CamcopsApp::~CamcopsApp()
{
    // http://doc.qt.io/qt-5.7/objecttrees.html
    // Only delete things that haven't been assigned a parent
    delete m_p_main_window;
}


int CamcopsApp::run()
{
    qDebug() << "CamcopsApp::run()";

    m_p_main_window = new QMainWindow();
    m_p_main_window->showMaximized();
    // m_p_main_window->showFullScreen();
    m_p_window_stack = new QStackedWidget(m_p_main_window);
    m_p_main_window->setCentralWidget(m_p_window_stack);

    MainMenu* menu = new MainMenu(*this);
    open(menu);

    qInfo() << "Starting Qt event processor...";
    return exec();  // Main Qt event loop
}


QSqlDatabase& CamcopsApp::db()
{
    return m_db;
}


QSqlDatabase& CamcopsApp::sysdb()
{
    return m_sysdb;
}


TaskFactoryPtr CamcopsApp::factory()
{
    return m_p_task_factory;
}


void CamcopsApp::open(OpenableWidget* widget, TaskPtr task,
                      bool may_alter_task)
{
    if (!widget) {
        qCritical() << "CamcopsApp::open: attempt to open nullptr";
        return;
    }

    Qt::WindowStates prev_window_state = m_p_main_window->windowState();
    QPointer<OpenableWidget> guarded_widget = QPointer<OpenableWidget>(widget);

    widget->build();
    qDebug() << "Pushing screen";
    int index = m_p_window_stack->addWidget(widget);
    // The stack takes over ownership.
    m_p_window_stack->setCurrentIndex(index);
    if (widget->wantsFullscreen()) {
        m_p_main_window->showFullScreen();
    }

    // 3. Signal
    connect(widget, &OpenableWidget::finished,
            this, &CamcopsApp::close);

    m_info_stack.push(OpenableInfo(guarded_widget, task, prev_window_state,
                                   may_alter_task));
    // This stores a QSharedPointer to the task (if supplied), so keeping that
    // keeps the task "alive" whilst its widget is doing things.
}


void CamcopsApp::close()
{
    if (m_info_stack.isEmpty()) {
        stopApp("No more windows; closing");
    }
    OpenableInfo info = m_info_stack.pop();
    // on function exit, will delete the task if it's the last pointer to it

    QWidget* top = m_p_window_stack->currentWidget();
    qDebug() << "Popping screen";
    m_p_window_stack->removeWidget(top);
    // Ownership is returned to the application, so...
    top->deleteLater();  // later, in case it was this object that called us

    m_p_main_window->setWindowState(info.prev_window_state);

    if (info.may_alter_task) {
        emit taskAlterationFinished(info.task);
    }
}


bool CamcopsApp::privileged() const
{
    return m_lockstate == LockState::Privileged;
}


bool CamcopsApp::locked() const
{
    return m_lockstate == LockState::Locked;
}


LockState CamcopsApp::lockstate() const
{
    return m_lockstate;
}


void CamcopsApp::setLockState(LockState lockstate)
{
    bool changed = lockstate != m_lockstate;
    m_lockstate = lockstate;
    if (changed) {
        emit lockStateChanged(lockstate);
    }
}


void CamcopsApp::unlock()
{
    // *** security check
    setLockState(LockState::Unlocked);
}


void CamcopsApp::lock()
{
    setLockState(LockState::Locked);
}


void CamcopsApp::grantPrivilege()
{
    // *** security check
    setLockState(LockState::Privileged);
}


bool CamcopsApp::whiskerConnected() const
{
    return m_whisker_connected;
}


void CamcopsApp::setWhiskerConnected(bool connected)
{
    bool changed = connected != m_whisker_connected;
    m_whisker_connected = connected;
    if (changed) {
        emit whiskerConnectionStateChanged(connected);
    }
}

bool CamcopsApp::patientSelected() const
{
    return m_patient_id != NONEXISTENT_PK;
}


QString CamcopsApp::patientDetails() const
{
    return "*** patient details ***";
}


void CamcopsApp::setSelectedPatient(int patient_id)
{
    bool changed = patient_id != m_patient_id;
    m_patient_id = patient_id;
    if (changed) {

    }
}


int CamcopsApp::currentPatientId() const
{
    return m_patient_id;
}


int CamcopsApp::fontSizePt(FontSize fontsize) const
{
    // *** font size: use configured variables instead
    switch (fontsize) {
    case FontSize::Normal:
    default:
        return 10;
    case FontSize::Big:
        return 12;
    case FontSize::Heading:
        return 16;
    case FontSize::Title:
        return 20;
    }
}
