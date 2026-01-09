import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import TTSConfig from './TTSConfig';
import './AvatarSettingsModal.css'; // Reusable modal styles

export default function TTSConfigModal({ onClose, onSave, currentSettings }) {
    const { t } = useTranslation();
    const [tempConfig, setTempConfig] = useState(currentSettings);

    const handleConfirm = () => {
        if (tempConfig && onSave) {
            onSave(tempConfig);
        }
        onClose();
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content premium-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>

                <div className="modal-header">
                    <h2>🎙️ {t('settings.ttsTitle')}</h2>
                    <p className="modal-subtitle">{t('settings.ttsSubtitle')}</p>
                </div>

                <div className="modal-body p-5">
                    <TTSConfig
                        onConfigChange={(config) => setTempConfig(config)}
                        initialConfig={currentSettings}
                    />
                </div>

                <div className="modal-footer-actions">
                    <button className="confirm-btn premium-button" onClick={handleConfirm}>
                        {t('action.confirm')}
                    </button>
                </div>
            </div>
        </div>
    );
}

