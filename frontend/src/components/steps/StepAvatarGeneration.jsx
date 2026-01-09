import React, { useState, useEffect } from 'react';
import { getSystemInfo } from '../../services/avatarService';
import { api } from '../../services/api';
import '../ColabModal.css';

export default function StepAvatarGeneration({
    avatarConfig,
    started,
    progress,
    audioCompleted,
    onStart,
    onPreview,
    onRegenerate,
    onNext
}) {
    const [showColab, setShowColab] = useState(false);
    const [systemBusy, setSystemBusy] = useState(false);
    const [busyMessage, setBusyMessage] = useState('');

    // Poll system status to detect concurrency
    useEffect(() => {
        let isMounted = true;
        const checkStatus = async () => {
            try {
                const info = await getSystemInfo();
                if (isMounted) {
                    if (info.is_generating) {
                        setSystemBusy(true);
                        setBusyMessage(info.busy_message || 'System is busy generating video...');
                    } else {
                        setSystemBusy(false);
                        setBusyMessage('');
                    }
                }
            } catch (e) {
                if (isMounted) {
                    // Only log if still mounted to avoid noise when navigating away
                    console.warn("Failed to check system status", e.message);
                }
            }
        };

        const timer = setInterval(checkStatus, 10000); // Check every 10s
        checkStatus();
        return () => { isMounted = false; clearInterval(timer); };
    }, []);

    // Inline Safe Styles with CSS Variables for Theme Adaptability
    const containerStyle = {
        marginTop: '30px',
        padding: '24px',
        backgroundColor: 'var(--color-bg-secondary)', // Adaptive Background
        borderRadius: '16px',
        border: '1px solid var(--color-surface)',     // Adaptive Border
        boxShadow: 'var(--shadow-lg)',
        color: 'var(--color-text)'                    // Adaptive Text
    };

    const headerStyle = {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px',
        marginBottom: '24px',
        borderBottom: '1px solid var(--color-surface)',
        paddingBottom: '16px'
    };

    const cardContainerStyle = {
        display: 'flex',
        gap: '20px',
        flexDirection: 'row', // Force row layout
        alignItems: 'stretch'
    };

    const cardStyle = {
        flex: 1,
        backgroundColor: 'var(--color-surface)', // Adaptive Surface
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid var(--color-surface-hover)',
        display: 'flex',
        flexDirection: 'column'
    };

    const badgeStyle = {
        display: 'inline-block',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold',
        marginBottom: '12px'
    };

    // HIGH CONTRAST CODE STYLE (Dark BG + Amber Text)
    // Works perfectly on both Light (White) and Dark (Black) themes
    const codeStyle = {
        fontFamily: 'monospace',
        backgroundColor: '#334155',  // Solid Dark Slate
        color: '#fbbf24',            // Bright Amber 
        padding: '2px 8px',
        borderRadius: '4px',
        fontWeight: 'bold',
        border: '1px solid #475569'
    };

    const currentEmotion = avatarConfig?.emotion || 4; // Default to 4 if missing

    return (
        <div className={`stage-view stage-avatar fade-in`}>
            {avatarConfig ? (
                <>
                    <div className="stage-hero">
                        <div className="hero-icon animated-scan">🎭</div>
                        <div className="stage-info">
                            <h3>第六步：影片強化 (選用)</h3>
                            <p>正在利用 Ditto 引擎將語音與照片結合，生成栩栩如生的播報影片...</p>
                        </div>
                    </div>

                    {!started ? (
                        <div className="manual-trigger-container">
                            <div className="info-box mb-6">
                                <p>語音檔已就緒。點擊下方按鈕開始為每頁投影片渲染播報員影片。</p>
                            </div>

                            {systemBusy && (
                                <div className="alert alert-warning mb-6" style={{ backgroundColor: '#fff3cd', color: '#856404', padding: '1rem', borderRadius: '0.25rem', border: '1px solid #ffeeba' }}>
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <strong>🚧 系統忙碌中</strong>
                                            <p>{busyMessage}</p>
                                        </div>
                                        <button
                                            className="btn btn-sm btn-outline-danger ml-4"
                                            onClick={async () => {
                                                if (confirm('確定要強制解除鎖定嗎？這可能會中斷正在進行的任務。')) {
                                                    try {
                                                        await api.forceUnlock();
                                                        setSystemBusy(false);
                                                        setBusyMessage('');
                                                        alert('已解除鎖定！請重新嘗試生成。');
                                                    } catch (e) {
                                                        alert('解除失敗: ' + e.message);
                                                    }
                                                }
                                            }}
                                            style={{ borderColor: '#d39e00', color: '#d39e00', backgroundColor: 'transparent' }}
                                        >
                                            🔓 強制解除鎖定
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-4">
                                <button
                                    className="btn btn-primary btn-xl flex-1"
                                    onClick={onStart}
                                    disabled={!audioCompleted || systemBusy}
                                >
                                    🎬 開始生成播報員影片
                                </button>
                                <button
                                    className="btn btn-secondary btn-xl flex-1"
                                    id="test-gen-btn"
                                    onClick={onPreview}
                                    disabled={!audioCompleted || systemBusy}
                                    title="僅生成 5 秒片段以確認臉部動作"
                                >
                                    🧪 測試生成 (5秒)
                                </button>
                            </div>

                            {/* Colab Guide - Opens in New Window */}
                            <button
                                className="colab-trigger-btn"
                                id="colab-trigger-btn"
                                onClick={() => window.open('/colab-guide.html', 'ColabGuide', 'width=1200,height=800,menubar=no,toolbar=no')}
                            >
                                <span className="icon">🚀</span>
                                <div className="text">
                                    <h4>Google Colab 雲端加速</h4>
                                    <p>本機跑太慢？使用免費 T4 GPU，速度提升 10 倍！</p>
                                </div>
                                <span className="badge" style={{ background: '#eab308', color: '#000', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>免費 GPU</span>
                                <span className="arrow">→</span>
                            </button>

                            {!audioCompleted && (
                                <p className="text-error mt-2">請先完成 Step 4 的語音生成</p>
                            )}
                        </div>
                    ) : (
                        <div className="stage-progress-wrapper">
                            <div className="progress-details">
                                <span className="percent">{progress.progress}%</span>
                                <span className="label">
                                    {progress.status === 'completed' ? '影片合成完成' : '影像渲染中...'}
                                </span>
                            </div>
                            <div className="progress-bar-bg large">
                                <div className="progress-bar-fill avatar-color" style={{ width: `${progress.progress}%` }}></div>
                            </div>

                            {progress.current_frame && (
                                <div className="mt-4 flex justify-center">
                                    <div className="frame-preview-container">
                                        <p className="text-sm text-gray-400 mb-2">即時預覽</p>
                                        <img
                                            src={`data:image/jpeg;base64,${progress.current_frame}`}
                                            alt="Current Frame"
                                            className="shadow-xl border-4 border-white/30"
                                            style={{ maxHeight: '200px', width: '200px', objectFit: 'cover', borderRadius: '50%', aspectRatio: '1' }}
                                        />
                                    </div>
                                </div>
                            )}
                            <p className="status-msg-large">{progress.message}</p>

                            {progress.status === 'completed' && (
                                <div className="mt-6 mb-4 w-full flex flex-col items-center animate-fade-in-up">
                                    {(progress.video_url || (progress.results && progress.results[0])) && (
                                        <div className="video-preview-wrapper w-full max-w-lg">
                                            <p className="text-sm text-gray-400 mb-2 text-center">
                                                {progress.video_url ? '✨ 測試生成預覽' : '✨ 第一張投影片預覽'}
                                            </p>
                                            <video
                                                controls
                                                className="w-full rounded-lg shadow-2xl border border-gray-700 bg-black aspect-square object-contain"
                                                src={`${api.API_BASE_URL || ''}${progress.video_url || progress.results[0]}`}
                                            />
                                        </div>
                                    )}
                                </div>
                            )}

                            {progress.status === 'processing' && (
                                <button className="btn btn-secondary-sm mt-6 text-gray-400 hover:text-white" onClick={onRegenerate}>⛔ 取消並重新開始</button>
                            )}

                            {progress.status === 'completed' && (
                                <div className="mt-8 flex justify-between items-center">
                                    <button className="btn btn-secondary-sm" onClick={onRegenerate}>↺ 重新生成影片</button>
                                    <button
                                        className="btn btn-primary text-sm font-semibold h-10 min-h-0 px-6 rounded-full shadow-lg"
                                        onClick={onNext}
                                    >
                                        更新 PPT (插入影片) ↻
                                    </button>
                                </div>
                            )}
                            {progress.status === 'failed' && (
                                <button className="btn btn-danger btn-lg mt-4 w-full" onClick={onRegenerate}>重試影片生成</button>
                            )}
                        </div>
                    )}
                </>
            ) : (
                <div className="stage-hero">
                    <div className="hero-icon">🚫</div>
                    <div className="stage-info">
                        <h3>無播報員配置</h3>
                        <p>您在設定階段未開啟數位播報員功能，此步驟已跳過。</p>
                        <button className="btn btn-primary mt-4" onClick={onNext}>前往下一階段: PPT 封裝 →</button>
                    </div>
                </div>
            )}
        </div>
    );
}
