#include "waitbox.h"
#include <QApplication>
#include <QDebug>
#include <QThread>

/*

  - Wait cursor:
    http://stackoverflow.com/questions/13495283/change-cursor-to-hourglass-wait-busy-cursor-and-back-in-qt

  - Doing something and showing a wait indicator:

    - All Qt UI elements must be created in the GUI thread.
        http://doc.qt.io/qt-5/thread-basics.html#gui-thread-and-worker-thread

    - So the wait box must be run from the main thread.

    - A QProgressDialog is a bit unreliable; it seems to require an uncertain
      number of calls to setValue(), even with setMinimumDuration(0), before
      it's fully painted. If you create it and give a single call (or 5, or 10)
      to setValue(), you can get just part of the dialog painted.

      Looks nice, though, with min = max = 0 for an "infinite wait" bar.

    - So, better would be a different QDialog?
      ... No, that too fails to be painted properly.

    - Therefore, threads:
      (1) Start on GUI thread.
          - GUI thread starts worker thread (2).
          - GUI thread opens progress dialog modally, and sits in its exec()
            loop, thus processing events but blocking from the point of view
            of the calling code.
          - GUI thread returns when signalled.
      (2) Worker thread starts, taking callback as argument.
          - Worker thread does work.
          - Worker thread signals GUI thread when done.

    - OK! That's great for non-GUI work.

    - Others' thoughts (for non-GUI work), using QtConcurrent:
      http://stackoverflow.com/questions/22670564/reliably-showing-a-please-wait-dialog-while-doing-a-lengthy-blocking-operation

    - Any way to pop up a wait dialogue when we're waiting for a slow GUI
      operation? That's less obvious...
      Achieved pretty well using SlowGuiGard class; q.v.


*/




WaitBox::WaitBox(QWidget* parent, const QString& text, const QString& title,
                 int minimum_duration_ms) :
    QProgressDialog(text, "", 0, 0, parent)
{
    // if min = max = 0, you get an infinite wait bar.

    // qDebug() << Q_FUNC_INFO;
    QApplication::setOverrideCursor(Qt::WaitCursor);
    setWindowTitle(title);
    setWindowModality(Qt::WindowModal);
    setCancelButton(nullptr);

    // Without the setMinimumDuration() call, you never see the dialog.
    setMinimumDuration(minimum_duration_ms);
}


WaitBox::~WaitBox()
{
    // qDebug() << Q_FUNC_INFO;
    QApplication::restoreOverrideCursor();
    // qDebug() << Q_FUNC_INFO << "done";
}
