import { useState } from 'react';
import TTSConfig from './TTSConfig';
import './AvatarSettingsModal.css'; // Reusable modal styles

export default function TTSConfigModal({ onClose, onSave, currentSettings }) {
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
                    <h2>🎙️ 語音合成設定</h2>
                    <p className="modal-subtitle">設定預設的語音模型與速率</p>
                </div>

                <div className="modal-body p-5">
                    <TTSConfig
                        onConfigChange={(config) => setTempConfig(config)}
                        initialConfig={currentSettings}
                    />
                </div>

                <div className="modal-footer-actions">
                    <button className="confirm-btn premium-button" onClick={handleConfirm}>
                        確認
                    </button>
                </div>
            </div>
        </div>
    );
}
