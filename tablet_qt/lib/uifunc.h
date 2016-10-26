#pragma once
#include <QObject>
#include <QSize>
#include <QString>

class QAbstractButton;
class QLabel;
class QLayout;
class QPainter;
class QPointF;
class QPushButton;
class QStyleOptionButton;


namespace UiFunc {

    // ========================================================================
    // Translation convenience function
    // ========================================================================

    QString tr(const char* text);

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
    QString resourceFilename(const QString& resourcepath);
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
    void repolish(QWidget* widget);
    void setProperty(QWidget* widget, const QString& property,
                     const QVariant& value, bool repolish = true);
    QString cssBoolean(bool value);
    // And some specific ones:
    void setPropertyItalic(QWidget* widget, bool italic, bool repolish = true);
    void setPropertyMissing(QWidget* widget, bool missing,
                            bool repolish = true);
    // Drawing text with alignment at a point (not a rectangle):
    void drawText(QPainter& painter, qreal x, qreal y, Qt::Alignment flags,
                  const QString& text, QRectF* boundingRect = 0);
    void drawText(QPainter& painter, const QPointF& point, Qt::Alignment flags,
                  const QString& text, QRectF* boundingRect = 0);

    QSize contentsMarginsAsSize(const QWidget* widget);
    QSize contentsMarginsAsSize(const QLayout* layout);
    QSize spacingAsSize(const QLayout* layout);
    QSize pushButtonSizeHintFromContents(const QPushButton* button,
                                         QStyleOptionButton* opt,
                                         const QSize& child_size);

    // Size policies that take a few statements to create:
    QSizePolicy horizExpandingHFWPolicy();
    QSizePolicy horizMaximumHFWPolicy();

    // ========================================================================
    // Killing the app
    // ========================================================================

    void stopApp(const QString& error);

    // ========================================================================
    // Alerts
    // ========================================================================

    void alert(const QString& text, const QString& title = QObject::tr("Alert"));

    // ========================================================================
    // Confirmation
    // ========================================================================

    bool confirm(const QString& text, const QString& title,
                 QString yes, QString no, QWidget* parent);

    // ========================================================================
    // Password checks/changes
    // ========================================================================

    bool getPassword(const QString& text, const QString& title,
                     QString& password, QWidget* parent);
    bool getOldNewPasswords(const QString& text, const QString& title,
                            bool require_old_password,
                            QString& old_password, QString& new_password,
                            QWidget* parent);

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
