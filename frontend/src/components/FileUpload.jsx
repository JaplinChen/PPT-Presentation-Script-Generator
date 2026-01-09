import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import './FileUpload.css';

function FileUpload({ onUploadSuccess }) {
    const { t } = useTranslation();
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [analysisProgress, setAnalysisProgress] = useState({ progress: 0, message: '' });
    const [error, setError] = useState(null);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(
        (e) => {
            e.preventDefault();
            setIsDragging(false);

            const droppedFile = e.dataTransfer.files[0];
            if (droppedFile && (droppedFile.name.endsWith('.ppt') || droppedFile.name.endsWith('.pptx'))) {
                setFile(droppedFile);
                setError(null);
            } else {
                setError(t('upload.supportFormat'));
            }
        },
        [t]
    );

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError(t('upload.selectFile'));
            return;
        }

        setIsUploading(true);
        setError(null);
        setAnalysisProgress({ progress: 10, message: t('upload.analyzing') });

        try {
            // Step 1: Upload (Quick)
            const uploadResponse = await api.uploadPPT(file);
            const fileId = uploadResponse.file_id;

            // Step 2: Polling (Robust)
            const pollStatus = async () => {
                try {
                    const statusData = await api.getParseStatus(fileId);

                    if (statusData.status === 'completed') {
                        if (onUploadSuccess) {
                            await onUploadSuccess(file, statusData);
                        }
                        return true;
                    } else if (statusData.status === 'failed') {
                        throw new Error(statusData.message || 'Analysis failed');
                    } else {
                        // Keep polling
                        setAnalysisProgress({
                            progress: statusData.progress || 50,
                            message: statusData.message || t('upload.analyzing')
                        });
                        return false;
                    }
                } catch (err) {
                    throw err;
                }
            };

            // Polling loop
            const poll = async () => {
                const isFinished = await pollStatus();
                if (!isFinished) {
                    setTimeout(poll, 2000); // Poll every 2 seconds
                }
            };

            await poll();

        } catch (err) {
            setError(err.message);
            setIsUploading(false);
        }
    };

    return (
        <div className="file-upload">
            <div
                className={`upload-area ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {!file ? (
                    <div className="upload-placeholder-content">
                        <div className="upload-icon" aria-hidden="true">
                            ⬆️
                        </div>
                        <div className="upload-text-group">
                            <h3>{t('upload.dragDrop')}</h3>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                                <label className="upload-button">
                                    {t('upload.selectFile') || 'Select File'}
                                    <input
                                        type="file"
                                        accept=".ppt,.pptx"
                                        onChange={handleFileSelect}
                                        style={{ display: 'none' }}
                                    />
                                </label>
                                <span className="upload-hint">{t('upload.supportFormat')}</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <>
                        <div className="file-info">
                            <div className="file-icon" aria-hidden="true">
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="ppt-svg-icon">
                                    <rect width="48" height="48" rx="8" fill="url(#ppt_gradient)" />
                                    <path d="M16 14H28C32.4183 14 36 17.5817 36 22C36 26.4183 32.4183 30 28 30H22V36H16V14ZM22 24V20H28C29.1046 20 30 20.8954 30 22C30 23.1046 29.1046 24 28 24H22Z" fill="white" />
                                    <defs>
                                        <linearGradient id="ppt_gradient" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                                            <stop stopColor="#D24726" />
                                            <stop offset="1" stopColor="#A3321A" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                            </div>
                            <div className="file-details">
                                <h4>{file.name}</h4>
                                <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        </div>
                        <button className="change-file-btn" onClick={() => setFile(null)}>
                            {t('upload.reupload')}
                        </button>
                    </>
                )}
            </div>

            {error && <div className="error-message">⚠️ {error}</div>}

            {file && !isUploading && (
                <button className="btn btn-primary upload-submit-btn" onClick={handleUpload}>
                    {t('upload.startAnalyze') || 'Analyze'}
                </button>
            )}

            {isUploading && (
                <div className="uploading-indicator">
                    <div className="spinner"></div>
                    <div className="progress-info">
                        <p>{analysisProgress.message || t('upload.analyzing')}</p>
                        {analysisProgress.progress > 0 && (
                            <div className="progress-bar-container">
                                <div
                                    className="progress-bar-fill"
                                    style={{ width: `${analysisProgress.progress}%` }}
                                ></div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default FileUpload;
