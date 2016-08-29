#pragma once
#include <QPixmap>
#include <QPushButton>
#include <QSize>


class ImageButton : public QPushButton
{
    // Button that shows a CamCOPS icon image, and another when being pressed.
    // This should be more efficient than an equivalent method using
    // stylesheets, and also allows the use of the global QPixmapCache.

    Q_OBJECT
public:
    ImageButton(QWidget* parent = nullptr);
    ImageButton(const QString& normal_filename,
                const QString& pressed_filename,
                const QSize& size = QSize(),
                QWidget* parent = nullptr);
    ImageButton(const QString& base_filename,
                bool filename_is_camcops_stem = true,
                bool alter_unpressed_image = true,
                bool disabled = false,
                QWidget* parent = nullptr);  // Default button maker
    void setImages(const QString& base_filename,
                   bool filename_is_camcops_stem = true,
                   bool alter_unpressed_image = true,
                   bool pressed_marker_behind = true,
                   bool disabled = false,
                   bool read_only = false);
    void setNormalImage(const QString& filename, const QSize& size = QSize(),
                        bool cache = true);
    void setNormalImage(const QPixmap& pixmap, bool scale = true);
    void setPressedImage(const QString& filename, const QSize& size = QSize(),
                         bool cache = true);
    void setPressedImage(const QPixmap& pixmap, bool scale = true);
    QSize sizeHint() const;
    void setImageSize(const QSize& size, bool scale = false);
    void setAsText(bool as_text);
    void resizeImages(double factor);
protected:
    void commonConstructor(const QSize& size);
    virtual void paintEvent(QPaintEvent *e);
    void rescale(QPixmap& pm);
    void resizeIfNoSize();
protected:
    bool m_as_text;
    QPixmap m_normal_pixmap;
    QPixmap m_pressed_pixmap;
    QSize m_image_size;
};