import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { avatarStorage } from '../services/avatarStorage';
import './ScriptConfig.css';

function ScriptConfig({ onGenerate, isGenerating }) {
    const { t, i18n } = useTranslation();

    const [config, setConfig] = useState(() => {
        try {
            const saved = localStorage.getItem('scriptConfig');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            console.error('Failed to load saved config:', e);
        }

        return {
            audience: '',
            purpose: '',
            context: 'Formal meeting',
            tone: 'Professional and natural',
            duration_sec: 600,
            include_transitions: true,
            language: 'Traditional Chinese'
        };
    });

    useEffect(() => {
        const langMap = {
            'zh-TW': 'Traditional Chinese',
            en: 'English',
            ja: 'Japanese',
            vi: 'Vietnamese'
        };
        const currentLang = i18n.language;
        if (langMap[currentLang]) {
            setConfig((prev) => ({ ...prev, language: langMap[currentLang] }));
        }
    }, [i18n.language]);

    // Save config to localStorage whenever it changes
    useEffect(() => {
        try {
            localStorage.setItem('scriptConfig', JSON.stringify(config));
        } catch (e) {
            console.error('Failed to save config:', e);
        }
    }, [config]);

    const handleChange = (field, value) => {
        setConfig((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        // Get avatar name for script customization
        const defaultPhoto = avatarStorage.getDefaultPhoto();
        const avatarName = defaultPhoto?.name;

        if (onGenerate) {
            onGenerate({
                ...config,
                audience: config.audience || t('options.audience.general'),
                purpose: config.purpose || t('config.purposePlaceholder'),
                avatar_name: avatarName
            });
        }
    };

    const audienceChips = [
        { label: t('options.audience.general'), color: 'default' },
        { label: t('options.audience.executives'), color: 'purple' },
        { label: t('options.audience.clients'), color: 'blue' },
        { label: t('options.audience.techTeam'), color: 'green' }
    ];

    return (
        <div className="script-config">
            <h2>⚙️ {t('config.title')}</h2>
            <form onSubmit={handleSubmit}>
                <div className="config-grid">
                    <div className="config-field">
                        <label>{t('config.audience')}</label>

                        <div className="audience-chips">
                            {audienceChips.map((opt) => (
                                <button
                                    type="button"
                                    key={opt.label}
                                    className={`chip chip-${opt.color} ${config.audience === opt.label ? 'active' : ''}`}
                                    onClick={() => handleChange('audience', opt.label)}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="config-field">
                        <label>{t('config.purpose')}</label>
                        <input
                            type="text"
                            value={config.purpose}
                            onChange={(e) => handleChange('purpose', e.target.value)}
                            placeholder={t('config.purposePlaceholder')}
                        />
                    </div>

                    <div className="config-row-group">
                        <div className="config-field">
                            <label>{t('config.context')}</label>
                            <select value={config.context} onChange={(e) => handleChange('context', e.target.value)}>
                                <option value="Formal meeting">{t('options.context.formalMeeting')}</option>
                                <option value="Internal sharing">{t('options.context.internalSharing')}</option>
                                <option value="Client proposal">{t('options.context.clientProposal')}</option>
                                <option value="Training">{t('options.context.training')}</option>
                                <option value="Seminar">{t('options.context.seminar')}</option>
                            </select>
                        </div>

                        <div className="config-field">
                            <label>{t('config.tone')}</label>
                            <select value={config.tone} onChange={(e) => handleChange('tone', e.target.value)}>
                                <option value="Professional and natural">{t('options.tone.professional')}</option>
                                <option value="Friendly and warm">{t('options.tone.friendly')}</option>
                                <option value="Serious">{t('options.tone.serious')}</option>
                                <option value="Energetic">{t('options.tone.enthusiastic')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="config-row-group">
                        <div className="config-field">
                            <label>{t('config.duration')}</label>
                            <input
                                type="number"
                                min="1"
                                max="60"
                                value={config.duration_sec ? config.duration_sec / 60 : ''}
                                onChange={(e) => {
                                    const val = parseInt(e.target.value, 10);
                                    handleChange('duration_sec', isNaN(val) ? 0 : val * 60);
                                }}
                            />
                        </div>

                        <div className="config-field">
                            <label>{t('config.outputLanguage')}</label>
                            <select value={config.language || 'Traditional Chinese'} onChange={(e) => handleChange('language', e.target.value)}>
                                <option value="Traditional Chinese">繁體中文</option>
                                <option value="English">English</option>
                                <option value="Japanese">日本語</option>
                                <option value="Vietnamese">Tiếng Việt</option>
                            </select>
                        </div>
                    </div>

                    <div className="config-field config-checkbox">
                        <label>
                            <input
                                type="checkbox"
                                checked={config.include_transitions}
                                onChange={(e) => handleChange('include_transitions', e.target.checked)}
                            />
                            <span>{t('config.transitions')}</span>
                        </label>
                    </div>
                </div>


                <button type="submit" className="btn btn-primary generate-btn" disabled={isGenerating}>
                    {isGenerating ? (
                        <>
                            <div className="btn-spinner"></div>
                            {t('config.generating')}
                        </>
                    ) : (
                        <>▶ {t('config.generateBtn')}</>
                    )}
                </button>
            </form>
        </div>
    );
}

export default ScriptConfig;
