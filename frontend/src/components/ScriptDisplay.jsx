import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useScriptEditing } from '../hooks/useScriptEditing';
import TTSConfig from './TTSConfig';
import { api, API_BASE_URL } from '../services/api';
import './ScriptDisplay.css';
import './ScriptDisplay_cards.css';

function ScriptDisplay({ scriptData: initialScriptData, slides, fileId, onStartNarrated, ttsConfig, onTTSConfigChange }) {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState('opening'); // 'opening' | 'slides'
    const [activeAudioId, setActiveAudioId] = useState(null);
    const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [copiedIndex, setCopiedIndex] = useState(null);

    useEffect(() => {
        if (initialScriptData?.metadata?.language && onTTSConfigChange) {
            const langMap = {
                'Traditional Chinese': 'zh',
                English: 'en',
                Japanese: 'ja',
                Vietnamese: 'vi'
            };
            const targetLang = langMap[initialScriptData.metadata.language];
            if (targetLang && (!ttsConfig.language || !ttsConfig.language.startsWith(targetLang))) {
                onTTSConfigChange({
                    ...ttsConfig,
                    language: targetLang,
                    voice: targetLang === 'zh' ? 'zh-TW-HsiaoChenNeural' : ''
                });
            }
        }
    }, [initialScriptData, ttsConfig.language, onTTSConfigChange]);

    const { localScriptData, editingIndex, editText, setEditText, startEditing, cancelEditing, saveEditing } =
        useScriptEditing(initialScriptData);

    // 使用 useCallback 優化，避免不必要的重新渲染
    // Fallback for non-HTTPS environments where navigator.clipboard is unavailable
    const handleCopy = useCallback((text, index = null) => {
        const copyToClipboard = (str) => {
            // Try modern clipboard API first
            if (navigator.clipboard && navigator.clipboard.writeText) {
                return navigator.clipboard.writeText(str);
            }
            // Fallback for HTTP environments
            const textArea = document.createElement('textarea');
            textArea.value = str;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            textArea.style.top = '-9999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
            } catch (err) {
                console.error('Fallback copy failed:', err);
            }
            document.body.removeChild(textArea);
            return Promise.resolve();
        };

        copyToClipboard(text).then(() => {
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        });
    }, []);


    const handleDownload = useCallback(() => {
        const blob = new Blob([localScriptData.full_script], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'presentation_script.txt';
        a.click();
        URL.revokeObjectURL(url);
    }, [localScriptData.full_script]);


    const handleGenerateAudio = async (text, id) => {
        if (!ttsConfig || !text) return;

        setIsGeneratingAudio(true);
        setActiveAudioId(id);
        setAudioUrl(null);

        // Remove === Header ===, --- Slide X ---, and other special characters
        const cleanText = text
            .replace(/===.*?===/g, ' ')
            .replace(/---.*?---/g, ' ')
            .replace(/-{2,}/g, ' ') // Remove standalone dashes
            .replace(/[*()[\]/]/g, ' ')
            .trim();

        // Remove estimation text in brackets
        const finalCleanText = cleanText.replace(/\([約大概]*\s*\d+\s*[秒分鐘seconds]+\)/g, ' ').replace(/\s+/g, ' ').trim();

        try {
            const result = await api.generateTTSAudio({
                text: finalCleanText,
                voice: ttsConfig.voice,
                rate: ttsConfig.rate,
                pitch: ttsConfig.pitch
            });
            setAudioUrl(`${API_BASE_URL}${result.url_path}`);
        } catch (error) {
            console.error('Audio generation failed', error);
            alert(`${t('tts.generating')} failed: ${error.message}`);
            setActiveAudioId(null);
        } finally {
            setIsGeneratingAudio(false);
        }
    };

    return (
        <div className="script-display">
            <div className="script-header">
                <h2>{t('result.title')}</h2>
            </div>



            <div className="script-tabs-container">
                <div className="script-tabs">
                    <button className={`tab-btn ${activeTab === 'opening' ? 'active' : ''}`} onClick={() => setActiveTab('opening')}>
                        {t('result.opening')}
                    </button>
                    <button className={`tab-btn ${activeTab === 'slides' ? 'active' : ''}`} onClick={() => setActiveTab('slides')}>
                        {t('result.slides')}
                    </button>
                </div>

                <div className="script-actions-inline">


                    <button
                        className="btn-icon-action"
                        onClick={handleDownload}
                        title={t('result.download')}
                        style={{ marginLeft: '8px' }}
                    >
                        ⬇️
                    </button>
                </div>
            </div>

            <div className="script-content">
                {activeTab === 'slides' && (
                    <div className="script-cards-container">
                        {localScriptData.slide_scripts.map((item, index) => (
                            <div key={index} id={`script-card-${index}`} className={`script-card glass-card ${editingIndex === index ? 'editing' : ''}`}>
                                <div className="script-card-header">
                                    <div className="header-left">
                                        <span className="script-card-number">{t('preview.page', { page: item.slide_no })}</span>
                                        <h3 className="script-card-title">{item.title}</h3>
                                    </div>

                                    <div className="card-actions">
                                        {editingIndex === index ? (
                                            <>
                                                <button className="btn-card-action btn-save" onClick={() => saveEditing(index)} title={t('action.save')}>
                                                    💾
                                                </button>
                                                <button className="btn-card-action btn-cancel" onClick={cancelEditing} title={t('action.cancel')}>
                                                    ✖
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button
                                                    className={`btn-icon-action ${activeAudioId === index ? 'text-green-400 border-green-400' : ''}`}
                                                    onClick={() => handleGenerateAudio(item.script, index)}
                                                    title={t('tts.preview')}
                                                >
                                                    {activeAudioId === index && isGeneratingAudio ? '…' : '▶'}
                                                </button>
                                                <button className="btn-icon-action" onClick={() => startEditing(index, item.script)} title={t('action.edit')}>
                                                    ✏️
                                                </button>
                                                <button className="btn-icon-action" onClick={() => handleCopy(item.script, index)} title={t('result.copy')}>
                                                    {copiedIndex === index ? '✓' : '⧉'}
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {activeAudioId === index && audioUrl && (
                                    <div className="script-card-player-bar">
                                        <audio controls autoPlay src={audioUrl} className="w-full" />
                                        <a href={audioUrl} download={`slide_${item.slide_no}.mp3`} className="btn-secondary px-3 py-1 text-sm whitespace-nowrap">
                                            ⬇️ MP3
                                        </a>
                                    </div>
                                )}

                                <div className="script-card-body">
                                    {editingIndex === index ? (
                                        <textarea className="script-edit-textarea" value={editText} onChange={(e) => setEditText(e.target.value)} autoFocus />
                                    ) : (
                                        <p>{item.script}</p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'opening' && (
                    <div className="script-section-card glass-card">
                        <div className="flex items-center justify-between mb-4 border-b border-gray-700 pb-2">
                            <h3>{t('result.opening')}</h3>
                            <div className="card-actions" style={{ display: 'flex', gap: '8px' }}>
                                {editingIndex === 'opening' ? (
                                    <>
                                        <button className="btn-card-action btn-save" onClick={() => saveEditing('opening')} title={t('action.save')}>
                                            💾
                                        </button>
                                        <button className="btn-card-action btn-cancel" onClick={cancelEditing} title={t('action.cancel')}>
                                            ✖
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button
                                            className={`btn-icon-action ${activeAudioId === 'opening' ? 'text-green-400 border-green-400' : ''}`}
                                            onClick={() => handleGenerateAudio(localScriptData.opening, 'opening')}
                                            title={t('tts.preview')}
                                        >
                                            {activeAudioId === 'opening' && isGeneratingAudio ? '…' : '▶'}
                                        </button>
                                        <button className="btn-icon-action" onClick={() => startEditing('opening', localScriptData.opening)} title={t('action.edit')}>
                                            ✏️
                                        </button>
                                        <button className="btn-icon-action" onClick={() => handleCopy(localScriptData.opening, 'opening')} title={t('result.copy')}>
                                            {copiedIndex === 'opening' ? '✓' : '⧉'}
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        {activeAudioId === 'opening' && audioUrl && (
                            <div className="mb-4 p-3 bg-gray-800 rounded border border-gray-600 flex items-center gap-3">
                                <audio controls autoPlay src={audioUrl} className="flex-1 h-10" />
                                <a href={audioUrl} download="opening.mp3" className="btn-secondary px-3 py-1 text-sm">
                                    ⬇️ MP3
                                </a>
                            </div>
                        )}

                        <div className="script-card-body">
                            {editingIndex === 'opening' ? (
                                <textarea className="script-edit-textarea" value={editText} onChange={(e) => setEditText(e.target.value)} autoFocus />
                            ) : (
                                <p className="script-text">{localScriptData.opening}</p>
                            )}
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}

export default ScriptDisplay;
