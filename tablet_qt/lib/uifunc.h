#pragma once
#include <QObject>
#include <QSize>
#include <QString>

class QAbstractButton;
class QLabel;


namespace UiFunc {

    // ========================================================================
    // QPixmap loader
    // ========================================================================

    QPixmap getPixmap(const QString& filename, const QSize& size = QSize(),
                      bool cache = true);

    // ========================================================================
    // Icons
    // ========================================================================

    QLabel* iconWidget(const QString& filename,
                       QWidget* parent = nullptr,
                       bool scale = true);
    QPixmap addCircleBackground(const QPixmap& image, const QColor& colour,
                                bool behind = true,
                                qreal pixmap_opacity = 1.0);
    QPixmap addPressedBackground(const QPixmap& image, bool behind = true);
    QPixmap addUnpressedBackground(const QPixmap& image, bool behind = true);
    QPixmap makeDisabledIcon(const QPixmap& image);
    QLabel* blankIcon(QWidget* parent);
    QString iconFilename(const QString& basefile);

    // ========================================================================
    // Buttons
    // ========================================================================

    QString iconButtonStylesheet(const QString& normal_filename,
                                 const QString& pressed_filename);
    QAbstractButton* iconButton(const QString& normal_filename,
                                const QString& pressed_filename = "",
                                QWidget* parent = nullptr);
    // QString iconPngFilename(const QString& stem);
    // QString iconTouchedPngFilename(const QString& stem);

    // ========================================================================
    // Widget manipulations, and other Qt internals
    // ========================================================================

    // QString cssColour(const QColor& colour);
    // void setBackgroundColour(QWidget* widget, const QColor& colour);
    void removeAllChildWidgets(QObject* object);
    Qt::Alignment combineAlignment(Qt::Alignment halign, Qt::Alignment valign);

    // ========================================================================
    // Killing the app
    // ========================================================================

    void stopApp(const QString& error);

    // ========================================================================
    // Alerts
    // ========================================================================

    void alert(const QString& text, const QString& title = QObject::tr("Alert"));

    // ========================================================================
    // Fonts; CSS
    // ========================================================================

    QString textCSS(int fontsize_pt, bool bold = false, bool italic = false,
                    const QString& colour = "");

    // ========================================================================
    // Opening URLS
    // ========================================================================

    void visitUrl(const QString& url);

}
