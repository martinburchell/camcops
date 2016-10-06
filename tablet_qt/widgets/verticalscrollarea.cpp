#include "verticalscrollarea.h"
#include <QDebug>
#include <QEvent>
#include <QScrollBar>


VerticalScrollArea::VerticalScrollArea(QWidget* parent) :
    QScrollArea(parent)
{
    setWidgetResizable(true);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    // RNC addition:
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);

    setSizeAdjustPolicy(QAbstractScrollArea::AdjustToContents);
}


bool VerticalScrollArea::eventFilter(QObject* o, QEvent* e)
{
    // This works because QScrollArea::setWidget installs an eventFilter on the
    // widget
    if (o && o == widget() && e && e->type() == QEvent::Resize) {
        // RNC: HORIZONTAL: this plus the Expanding policy.
        setMinimumWidth(widget()->minimumSizeHint().width() +
                        verticalScrollBar()->width());

        // RNC:
        // qDebug().nospace()
        //         << "VerticalScrollArea::eventFilter [QEvent::Resize]"
        //         << "; minimumHeight(): " << minimumHeight()
        //         << "; minimumSizeHint(): " << minimumSizeHint()
        //         << "; size(): " << size()
        //         << "; sizeHint(): " << sizeHint()
        //         << "; widget()->size(): " << widget()->size()
        //         << "; widget()->sizeHint(): " << widget()->sizeHint();

        // If the scrollbox starts out small (because its contents are small),
        // and the contents grow, we will learn about it here -- and we need
        // to grow ourselves. When your sizeHint() changes, you should call
        // updateGeometry().

        // Except...
        // http://doc.qt.io/qt-5/qwidget.html
        // Warning: Calling setGeometry() inside resizeEvent() or moveEvent()
        // can lead to infinite recursion.
        // ... and we certainly had infinite recursion.
        // One way in which this can happen:
        // http://stackoverflow.com/questions/9503231/strange-behaviour-overriding-qwidgetresizeeventqresizeevent-event

        // NO? // updateGeometry();  // even contained text scroll areas work without it
        return false;  // DEFINITELY NEED THIS, NOT FALL-THROUGH TO PARENT
    } else {
        return QScrollArea::eventFilter(o, e);
    }
}


// RNC addition:
// VERTICAL.
// Without this (and a vertical size policy of Maximum), it's very hard to
// get the scroll area to avoid one of the following:
// - expand too large vertically; distribute its contents vertically; thus
//   need an internal spacer at the end of its contents; thus have a duff
//   endpoint;
// - be too small vertically (e.g. if a spacer is put below it to prevent it
//   expanding too much) when there is vertical space available to use.
// So the answer is a Maximum vertical size policy, and a size hint that is
// exactly that of its contents.

QSize VerticalScrollArea::sizeHint() const
{
    // qDebug() << Q_FUNC_INFO << widget()->sizeHint();
    return widget()->sizeHint();
}
