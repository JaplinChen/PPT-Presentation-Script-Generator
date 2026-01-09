import { useState, useCallback } from 'react';
import { api } from '../services/api';
import './AvatarSettings.css';

export default function AvatarSettings({ onPhotoUploaded }) {
    const [isUploading, setIsUploading] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState(null);

    const processFile = async (file) => {
        if (!file) return;

        // Basic client-side checks
        if (!file.type.match('image.*')) {
            setError('請上傳 JPG 或 PNG 圖片檔案');
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            setError('檔案過大，請上傳小於 10MB 的圖片');
            return;
        }

        setIsUploading(true);
        setError(null);
        setUploadProgress(20);

        try {
            const photoData = await api.uploadAvatarPhoto(file);
            setUploadProgress(100);

            if (onPhotoUploaded) {
                onPhotoUploaded(photoData);
            }
        } catch (err) {
            console.error('Photo upload failed:', err);
            setError(err.message);
        } finally {
            setIsUploading(false);
            setIsDragging(false);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        processFile(file);
    };

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        processFile(file);
    }, []);

    return (
        <div className="avatar-upload-dropzone">
            <div
                className={`upload-inner-box ${isUploading ? 'is-uploading' : ''} ${isDragging ? 'is-dragging' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {isUploading ? (
                    <div className="uploading-state">
                        <div className="upload-spinner"></div>
                        <p>正在分析照片並驗證人臉...</p>
                        <div className="mini-progress-bar">
                            <div className="fill" style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                    </div>
                ) : (
                    <>
                        <label className="upload-trigger-label">
                            <div className="upload-icon">📸</div>
                            <div className="upload-text">
                                <strong>點擊或拖放照片到這裡</strong>
                                <span>建議使用正臉清楚的照片 (限制 10MB)</span>
                            </div>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                        </label>
                    </>
                )}
            </div>
            {error && <div className="upload-error">⚠️ {error}</div>}
        </div>
    );
}
