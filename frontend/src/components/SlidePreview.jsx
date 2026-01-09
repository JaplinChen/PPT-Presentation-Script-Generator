import { useTranslation } from 'react-i18next';
import './SlidePreview.css';

function SlidePreview({ slides }) {
    const { t } = useTranslation();

    if (!slides || slides.length === 0) return null;

    const scrollToSlide = (index) => {
        const element = document.getElementById(`script-card-${index}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    return (
        <div className="slide-preview-container">
            <h3>{t('preview.title')}</h3>

            <div className="slide-preview-list">
                {slides.map((slide, index) => (
                    <div
                        key={index}
                        className="slide-preview-item"
                        onClick={() => scrollToSlide(index)}
                    >
                        <div className="preview-header">
                            <span className="slide-number">{t('preview.page', { page: slide.slide_no })}</span>
                            {slide.image_count > 0 && (
                                <span className="image-badge">📷 {slide.image_count}</span>
                            )}
                        </div>
                        <div className="preview-content">
                            <h4>{slide.title || t('preview.noTitle')}</h4>
                            {slide.bullets && slide.bullets.length > 0 ? (
                                <ul className="slide-bullets">
                                    {slide.bullets.map((bullet, i) => (
                                        <li key={i}>{bullet}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="no-content">{t('preview.noContent')}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default SlidePreview;
