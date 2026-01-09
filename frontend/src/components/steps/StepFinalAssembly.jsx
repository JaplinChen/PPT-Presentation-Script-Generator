import React from 'react';
import { api } from '../../services/api';
import { getBackendUrl } from '../../services/config';

export default function StepFinalAssembly({
    scriptData,
    avatarConfig,
    started,
    progress,
    onStart,
    onRegenerate,
    onNext
}) {
    return (
        <div className={`stage-view stage-assemble fade-in`}>
            <div className="stage-hero">
                <div className="hero-icon animated-pulse" style={{ background: 'transparent', boxShadow: 'none', overflow: 'visible' }}>
                    <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', filter: 'drop-shadow(0 10px 20px rgba(208, 68, 35, 0.4))' }}>
                        <rect width="100" height="100" fill="#D04423" rx="22" />
                        <path d="M56 25 H 38 V 75 H 50 V 53 H 56 C 70 53 76 45 76 39 C 76 33 70 25 56 25 Z M 56 44 H 50 V 34 H 56 C 60 34 63 36 63 39 C 63 42 60 44 56 44 Z" fill="white" />
                        <path d="M85 25 L 65 25 L 65 75 L 85 75" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                    </svg>
                </div>
                <div className="stage-info">
                    <h3>第五步：PPT 製作</h3>
                    <p>正在整合語音與靜態播報員至投影片，並同步備註資訊...</p>
                </div>
            </div>

            {!started ? (
                <div className="manual-trigger-container">
                    <div className="info-box mb-6">
                        <p>音訊素材已準備就緒，點擊開始製作 PPT。</p>
                    </div>
                    <button
                        className="btn btn-primary btn-xl w-full"
                        onClick={onStart}
                    >
                        📦 開始製作 PPT
                    </button>
                </div>
            ) : (
                <div className="stage-progress-wrapper">
                    {progress.status !== 'completed' ? (
                        <>
                            <div className="progress-details">
                                <span className="percent">{progress.progress}%</span>
                                <span className="label">組裝中...</span>
                            </div>
                            <div className="progress-bar-bg large">
                                <div className="progress-bar-fill assemble-color" style={{ width: `${progress.progress}%` }}></div>
                            </div>
                            <p className="status-msg-large mb-4">{progress.message}</p>

                            {progress.status === 'failed' && (
                                <div className="text-center">
                                    <button className="btn btn-primary" onClick={onRegenerate}>↻ 重試封裝</button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="generation-success fadeIn">
                            {/* Header: Centered and Clean */}
                            <div className="flex items-center justify-center gap-2 mb-4">
                                <span className="text-3xl animate-bounce-slow">🎉</span>
                                <h2 className="text-xl font-bold text-slate-800 tracking-tight">製作完全達成！</h2>
                            </div>
                            <p className="text-slate-500 mb-6 font-medium text-sm">您的有聲影片 PPT 已經準備就緒，您可以點擊下方按鈕下載。</p>

                            {/* Stats: Premium Cards */}
                            <div className="success-stats flex justify-center gap-4 mb-12">
                                <div className="stat-item bg-white px-6 py-3 rounded-2xl border border-slate-100 shadow-sm flex flex-col items-center min-w-[110px] transition-all duration-300 hover:shadow-md hover:border-blue-200 hover:-translate-y-1 cursor-default group">
                                    <span className="stat-value text-xl font-extrabold text-slate-800 group-hover:text-blue-600 transition-colors">{scriptData?.slide_scripts?.length}</span>
                                    <span className="stat-label text-xs text-slate-400 mt-1 font-medium flex items-center gap-1">
                                        📄 投影片數
                                    </span>
                                </div>
                                {avatarConfig && (
                                    <div className="stat-item bg-white px-6 py-3 rounded-2xl border border-slate-100 shadow-sm flex flex-col items-center min-w-[110px] transition-all duration-300 hover:shadow-md hover:border-blue-200 hover:-translate-y-1 cursor-default group">
                                        <span className="stat-value text-xl font-extrabold text-slate-800 group-hover:text-blue-600 transition-colors">YES</span>
                                        <span className="stat-label text-xs text-slate-400 mt-1 font-medium flex items-center gap-1">
                                            👤 播報員
                                        </span>
                                    </div>
                                )}
                                <div className="stat-item bg-white px-6 py-3 rounded-2xl border border-slate-100 shadow-sm flex flex-col items-center min-w-[110px] transition-all duration-300 hover:shadow-md hover:border-blue-200 hover:-translate-y-1 cursor-default group">
                                    <span className="stat-value text-xl font-extrabold text-slate-800 group-hover:text-blue-600 transition-colors">FULL</span>
                                    <span className="stat-label text-xs text-slate-400 mt-1 font-medium flex items-center gap-1">
                                        ⚡ 模式
                                    </span>
                                </div>
                            </div>

                            {/* Buttons: Modern & Gradient */}
                            <div className="flex gap-4 justify-center items-center mt-4">
                                <a
                                    href={getBackendUrl(progress.result?.url_path)}
                                    className="btn border-0 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white px-8 text-sm font-semibold shadow-lg shadow-blue-200/50 rounded-full h-10 min-h-0 flex items-center gap-2 transform active:scale-95 transition-all"
                                    download
                                >
                                    📥 下載最終 PPT
                                </a>

                                {/* Optional: Go to Avatar Video Step */}
                                {onNext && (
                                    <button
                                        className="btn btn-primary px-8 text-sm font-semibold shadow-md rounded-full h-10 min-h-0 flex items-center gap-2 transform active:scale-95 transition-all"
                                        onClick={onNext}
                                    >
                                        ✨ 製作播報員影片
                                    </button>
                                )}
                            </div>

                            <button
                                className="btn-secondary-action mx-auto"
                                onClick={onRegenerate}
                            >
                                <span className="icon">↺</span>
                                <span>重新封裝</span>
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
