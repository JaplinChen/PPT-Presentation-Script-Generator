import { useState, useEffect } from 'react';
import { avatarStorage } from '../services/avatarStorage';
import AvatarSettings from './AvatarSettings';
import { API_BASE_URL } from '../services/api';
import './AvatarSettingsModal.css';

export default function AvatarSettingsModal({ onClose }) {
    const [settings, setSettings] = useState(avatarStorage.load());
    const [showUpload, setShowUpload] = useState(false);
    const [selectedPhoto, setSelectedPhoto] = useState(null);

    // Robust URL helper to handle missing paths
    const getFullUrl = (photo) => {
        if (!photo) return null;

        let url = photo.photo_url || photo.url_path;

        if (!url && photo.photo_id) {
            url = `/uploads/avatar_${photo.photo_id}.jpg`;
        }

        if (!url) return null;
        if (url.startsWith('http')) return url;

        // Ensure we don't have double slashes and use the imported API_BASE_URL
        const cleanUrl = url.startsWith('/') ? url : `/${url}`;
        const baseUrl = API_BASE_URL || window.location.origin; // Fix: use API_BASE_URL or relative to current origin
        return `${baseUrl}${cleanUrl}`;
    };

    useEffect(() => {
        const currentSettings = avatarStorage.load();
        setSettings(currentSettings);

        // Default select the preset photo or the first one
        // FIX: Don't auto-select to avoid blocking the view with the details popup
        // const defaultPhoto = avatarStorage.getDefaultPhoto();
        // setSelectedPhoto(defaultPhoto || currentSettings.photos[0] || null);
    }, []);

    const handleRename = (id, newName) => {
        const currentSettings = avatarStorage.load();
        const photoIdx = currentSettings.photos.findIndex(p => p.id === id);
        if (photoIdx !== -1) {
            currentSettings.photos[photoIdx].name = newName;
            avatarStorage.save(currentSettings);
            setSettings(currentSettings);
            if (selectedPhoto?.id === id) {
                setSelectedPhoto({ ...selectedPhoto, name: newName });
            }
        }
    };

    const handlePhotoUploaded = async (photoData) => {
        // Handle removal or cancellation
        if (!photoData) {
            // Optional: You might want to unset selectedPhoto if it was a draft, 
            // but here we just close the upload panel or do nothing.
            // setShowUpload(false); // Uncomment if we want to close on remove
            return;
        }

        const newPhoto = avatarStorage.addPhoto({
            photo_id: photoData.photo_id,
            photo_url: photoData.photo_url || photoData.url_path,
            name: `播報員 ${settings.photos.length + 1}`,
            validation: photoData.validation
        });

        const newSettings = avatarStorage.load();
        setSettings(newSettings);
        setSelectedPhoto(newPhoto);
        setShowUpload(false);
    };

    const handleSetDefault = (id) => {
        avatarStorage.setDefaultPhoto(id);
        const newSettings = avatarStorage.load();
        setSettings(newSettings);

        // Keep the selected photo data updated with isDefault flag
        const updatedPhoto = newSettings.photos.find(p => p.id === id);
        if (updatedPhoto) {
            setSelectedPhoto(updatedPhoto);
        }
    };

    const handleDelete = (id) => {
        if (window.confirm('Are you sure you want to remove this presenter?')) {
            avatarStorage.removePhoto(id);
            const newSettings = avatarStorage.load();
            setSettings(newSettings);
            if (selectedPhoto?.id === id) {
                setSelectedPhoto(newSettings.photos[0] || null);
            }
        }
    };

    const handleParamChange = (key, value) => {
        const newPrefs = { ...settings.preferences, [key]: value };
        avatarStorage.updatePreferences(newPrefs);
        setSettings(avatarStorage.load());
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content premium-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose} aria-label="關閉">×</button>

                <div className="avatar-settings-modal">
                    <header className="modal-header">
                        <div className="flex justify-between items-start">
                            <div>
                                <h2>🎭 數位播報員管理</h2>
                                <p className="modal-subtitle">點擊照片進行編輯或設定生成偏好</p>
                            </div>
                        </div>
                    </header>

                    <section className="photo-management-section">
                        <div className="photo-grid">
                            {settings.photos.map(photo => {
                                const photoUrl = getFullUrl(photo);
                                return (
                                    <div
                                        key={photo.id}
                                        className={`photo-card ${photo.isDefault ? 'is-default' : ''}`}
                                        onClick={() => setSelectedPhoto(photo)}
                                    >
                                        <div className="photo-card-inner">
                                            {photoUrl && <img
                                                src={photoUrl}
                                                alt={photo.name}
                                                className="photo-thumbnail"
                                                onError={(e) => {
                                                    const target = e.target;
                                                    const src = target.src;
                                                    if (target.dataset.retried === 'true') {
                                                        target.src = 'https://via.placeholder.com/150?text=No+Img';
                                                        return;
                                                    }
                                                    if (src.endsWith('.jpg')) {
                                                        target.src = src.replace('.jpg', '.png');
                                                        target.dataset.retried = 'true';
                                                    } else if (src.endsWith('.png')) {
                                                        target.src = src.replace('.png', '.jpg');
                                                        target.dataset.retried = 'true';
                                                    }
                                                }}
                                            />}
                                            {photo.isDefault && <div className="default-glow"></div>}
                                            {photo.isDefault && <span className="default-pill">預設</span>}
                                            <div className="photo-card-overlay">
                                                <span className="photo-name-display">{photo.name}</span>
                                            </div>
                                        </div>

                                        <div className="photo-card-actions" onClick={e => e.stopPropagation()}>
                                            <button
                                                className={`action-btn set-default ${photo.isDefault ? 'active' : ''}`}
                                                onClick={() => handleSetDefault(photo.id)}
                                                title="設為預設"
                                            >
                                                ⭐
                                            </button>
                                            <button
                                                className="action-btn delete"
                                                onClick={() => handleDelete(photo.id)}
                                                title="刪除"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}

                            <div className="photo-card add-new-card" onClick={() => setShowUpload(true)}>
                                <div className="add-inner">
                                    <span className="plus-icon">+</span>
                                    <span>新增照片</span>
                                </div>
                            </div>
                        </div>

                        {showUpload && (
                            <div className="upload-container-wrapper glass-card">
                                <div className="upload-header">
                                    <h4>上傳播報員照片</h4>
                                    <button className="close-upload" onClick={() => setShowUpload(false)}>取消</button>
                                </div>
                                <AvatarSettings onPhotoUploaded={handlePhotoUploaded} />
                            </div>
                        )}
                    </section>

                    {/* 細節編輯彈窗 (Popup Overlay) */}
                    {selectedPhoto && (
                        <div className="details-popup-overlay" onClick={() => setSelectedPhoto(null)}>
                            <div className="photo-details-container glass-card popup-mode" onClick={e => e.stopPropagation()}>
                                <button className="close-popup-btn" onClick={() => setSelectedPhoto(null)}>✕</button>

                                <div className="details-header-row">
                                    <div className="identity-block">
                                        <div className="editable-name-container">
                                            <input
                                                className="name-input"
                                                value={selectedPhoto.name}
                                                onChange={(e) => handleRename(selectedPhoto.id, e.target.value)}
                                                spellCheck="false"
                                                placeholder="輸入播報員名稱..."
                                                autoFocus
                                            />
                                            <span className="pencil-icon">✎</span>
                                        </div>
                                        <code className="photo-id-tag">照片 ID: {selectedPhoto.photo_id.split('-')[0]}...</code>
                                    </div>
                                    <div className={`verification-badge ${selectedPhoto.validation?.valid ? 'valid' : 'invalid'}`}>
                                        <span className="status-indicator"></span>
                                        {selectedPhoto.validation?.valid ? 'AI 驗證成功' : '驗證失敗'}
                                    </div>
                                </div>

                                <div className="details-main-content">
                                    <div className="preview-container">
                                        <div className="image-frame">
                                            {getFullUrl(selectedPhoto) ? (
                                                <img
                                                    src={getFullUrl(selectedPhoto)}
                                                    alt="已選播報員"
                                                    onError={(e) => {
                                                        const target = e.target;
                                                        const src = target.src;

                                                        // Prevent infinite loops
                                                        if (target.dataset.retried === 'true') {
                                                            target.src = 'https://via.placeholder.com/400x400?text=No+Image';
                                                            return;
                                                        }

                                                        // Try PNG if JPG failed (or vice versa)
                                                        if (src.endsWith('.jpg')) {
                                                            target.src = src.replace('.jpg', '.png');
                                                            target.dataset.retried = 'true';
                                                        } else if (src.endsWith('.png')) {
                                                            target.src = src.replace('.png', '.jpg');
                                                            target.dataset.retried = 'true';
                                                        } else {
                                                            // Fallback for other cases
                                                            target.src = 'https://via.placeholder.com/400x400?text=Image+Error';
                                                        }
                                                    }}
                                                />
                                            ) : (
                                                <div className="no-image-placeholder">無預覽圖</div>
                                            )}
                                            {(selectedPhoto.validation?.face_rect || selectedPhoto.validation?.face_bbox) && (
                                                <div className="face-boundary" style={(() => {
                                                    const v = selectedPhoto.validation;
                                                    if (v.face_rect) {
                                                        return {
                                                            top: `${v.face_rect.top}%`,
                                                            left: `${v.face_rect.left}%`,
                                                            width: `${v.face_rect.width}%`,
                                                            height: `${v.face_rect.height}%`
                                                        };
                                                    } else if (v.face_bbox) {
                                                        // Fallback for missing image_size
                                                        const [x, y, w, h] = v.face_bbox;
                                                        const imgW = v.image_size ? v.image_size[0] : 100;
                                                        const imgH = v.image_size ? v.image_size[1] : 100;
                                                        const isPercentage = imgW === 100;

                                                        return {
                                                            top: isPercentage ? `${y}%` : `${(y / imgH) * 100}%`,
                                                            left: isPercentage ? `${x}%` : `${(x / imgW) * 100}%`,
                                                            width: isPercentage ? `${w}%` : `${(w / imgW) * 100}%`,
                                                            height: isPercentage ? `${h}%` : `${(h / imgH) * 100}%`,
                                                            borderStyle: isPercentage ? 'dashed' : 'solid'
                                                        };
                                                    }
                                                    return { display: 'none' };
                                                })()}></div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="analysis-data">
                                        <div className="data-item">
                                            <label>AI 診斷結果</label>
                                            <div className="data-value">
                                                {selectedPhoto.validation?.message || '驗證通過，準備好進行生成任務。'}
                                            </div>
                                        </div>
                                        <div className="data-item">
                                            <label>人臉座標 (Face Stats)</label>
                                            <div className="data-value mono">
                                                {(() => {
                                                    const v = selectedPhoto.validation;
                                                    if (v?.face_rect) {
                                                        return `[X: ${v.face_rect.left.toFixed(1)}, Y: ${v.face_rect.top.toFixed(1)}]`;
                                                    } else if (v?.face_bbox) {
                                                        return `[X: ${v.face_bbox[0]}, Y: ${v.face_bbox[1]}, W: ${v.face_bbox[2]}, H: ${v.face_bbox[3]}]`;
                                                    }
                                                    return '無數據';
                                                })()}
                                            </div>
                                            <div className="absolute -bottom-5 left-0 w-full text-center text-[10px] text-white/50">
                                                生成範圍
                                            </div>
                                        </div>
                                        <div className="data-item helper">
                                            <p>💡 此播報員將被用在接下來生成的影片中。</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="popup-footer">
                                    <button className="confirm-btn premium-button" onClick={() => setSelectedPhoto(null)}>完成</button>
                                </div>
                            </div>
                        </div>
                    )}

                    <section className="global-preferences-section">
                        <header className="section-header">
                            <h3>⚙️ 偏好設定</h3>
                        </header>

                        <div className="params-grid">
                            <div className="params-row-2col">
                                <div className="control-card compact">
                                    <div className="control-header">
                                        <label>情緒強度 (Emotion)</label>
                                        <span className="value-label">{settings.preferences.emotion}</span>
                                    </div>
                                    <input
                                        type="range"
                                        className="premium-slider"
                                        min="0.1" max="10" step="0.1"
                                        value={settings.preferences.emotion}
                                        onChange={e => handleParamChange('emotion', parseFloat(e.target.value))}
                                    />
                                    <div className="slider-ticks">
                                        <span>自然</span>
                                        <span>熱烈</span>
                                    </div>
                                </div>
                                <div className="control-card compact">
                                    <div className="control-header">
                                        <label>生成流暢度 (Sampling Steps)</label>
                                        <span className="value-label">{settings.preferences.sampling_steps}</span>
                                    </div>
                                    <input
                                        type="range"
                                        className="premium-slider"
                                        min="10" max="100" step="5"
                                        value={settings.preferences.sampling_steps}
                                        onChange={e => handleParamChange('sampling_steps', parseInt(e.target.value))}
                                    />
                                    <div className="slider-ticks">
                                        <span>快速</span>
                                        <span>極致流暢</span>
                                    </div>
                                </div>
                            </div>

                            {/* Removed previous full-width container for Sampling Steps */}

                            <div className="control-card compact full-width">
                                <div className="control-header">
                                    <label>影片解析度 (Resolution)</label>
                                    <span className="info-tooltip" title="解析度僅影響畫面清晰度，不影響影片流暢度(FPS固定25)">ℹ️</span>
                                </div>
                                <div className="resolution-selector">
                                    {[
                                        { label: '標準 (480p)', size: 480, desc: '檔案最小，適合 PPT' },
                                        { label: '高清 (720p)', size: 720, desc: '畫質平衡' },
                                        { label: '超清 (1080p)', size: 1920, desc: '最佳畫質，檔案大' }
                                    ].map((opt) => (
                                        <button
                                            key={opt.size}
                                            className={`res-btn ${settings.preferences.max_size === opt.size ? 'active' : ''}`}
                                            onClick={() => {
                                                handleParamChange('max_size', opt.size);
                                                // Decouple steps updates so user can set them manually
                                            }}
                                        >
                                            <span className="res-name">{opt.label}</span>
                                            <span className="res-desc">{opt.desc}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>

                    <footer className="modal-footer-actions">
                        <button className="confirm-btn premium-button" onClick={onClose}>關閉</button>
                    </footer>
                </div>
            </div>
        </div>
    );
}
