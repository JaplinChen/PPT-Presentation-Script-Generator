import React from 'react';
import { useTranslation } from 'react-i18next';

export default function StepAudioGeneration({
    scriptData,
    started,
    progress,
    onStart,
    onRegenerate,
    onNext
}) {
    const { t } = useTranslation();

    return (
        <div className="stage-view stage-audio fade-in">
            {/* Hero Section */}
            <div className="stage-hero">
                <div className="hero-icon animated-pulse" style={{ background: 'transparent', boxShadow: 'none', overflow: 'visible' }}>
                    <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', filter: 'drop-shadow(0 10px 20px rgba(124, 58, 237, 0.4))' }}>
                        <rect width="100" height="100" fill="#7C3AED" rx="22" />
                        <path d="M50 25 C43 25 38 30 38 37 L 38 53 C38 60 43 65 50 65 C57 65 62 60 62 53 L 62 37 C62 30 57 25 50 25 Z" fill="white" />
                        <path d="M30 50 C30 60 38 68 47 70 L 47 75 L 42 75 L 42 80 L 58 80 L 58 75 L 53 75 L 53 70 C62 68 70 60 70 50" fill="none" stroke="white" strokeWidth="5" strokeLinecap="round" />
                    </svg>
                </div>
                <div className="stage-info">
                    <h3>{t('steps.audioGenTitle')}</h3>
                    <p>{t('steps.audioGenDescription')}</p>
                </div>
            </div>

            {!started ? (
                /* Initial State */
                <div className="max-w-md mx-auto manual-trigger-container">
                    <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200 mb-6 text-center shadow-sm">
                        <p className="text-slate-600 font-medium">
                            {t('steps.audioGenReady', { count: scriptData?.slide_scripts?.length || 0 })}
                        </p>
                    </div>
                    <button
                        className="w-full cursor-pointer border-none rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white shadow-lg shadow-violet-200/50 py-3 text-sm font-semibold transition-all transform active:scale-95 flex items-center justify-center gap-2"
                        onClick={onStart}
                    >
                        <span>▶️</span> {t('steps.startAudioGen')}
                    </button>
                </div>
            ) : (
                /* Progress State */
                <div className="stage-progress-wrapper max-w-lg mx-auto">
                    <div className="progress-details flex justify-between items-end mb-2">
                        <span className="label text-sm font-medium text-slate-600">
                            {progress.status === 'completed' ? t('steps.audioGenComplete') : t('steps.converting')}
                        </span>
                        <span className="percent text-sm font-bold text-violet-600">{progress.progress}%</span>
                    </div>

                    <div className="progress-bar-bg h-3 bg-slate-100 rounded-full overflow-hidden mb-4 border border-slate-200">
                        <div
                            className="progress-bar-fill h-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-300 ease-out"
                            style={{ width: `${progress.progress}%` }}
                        ></div>
                    </div>

                    <p className="status-msg-large text-center text-sm text-slate-500 mb-6 min-h-[20px]">{progress.message}</p>

                    {/* Emergency Reset Button for stuck states */}
                    {progress.status === 'processing' && (
                        <div className="mt-4 text-center">
                            <button
                                className="text-xs text-slate-400 hover:text-red-500 transition-colors underline decoration-slate-300 underline-offset-2 hover:decoration-red-300"
                                onClick={(e) => {
                                    e.preventDefault();
                                    // Use standard confirm for safety, logically consistent
                                    if (window.confirm(t('steps.forceRetry'))) {
                                        onStart();
                                        if (onRegenerate) onRegenerate();
                                    }
                                }}
                            >
                                {t('steps.forceRetry')}
                            </button>
                        </div>
                    )}

                    {/* Success Actions */}
                    {progress.status === 'completed' && (
                        <div className="flex flex-col items-center gap-4 mt-8 animate-fade-in-up">
                            <button
                                className="btn btn-primary rounded-full px-6 py-2 shadow-md shadow-blue-200/50 text-sm font-semibold transition-all transform active:scale-95 flex items-center gap-2 min-w-[160px] justify-center"
                                onClick={onNext}
                            >
                                {t('steps.continuePPT')} <span>→</span>
                            </button>

                            <button
                                className="text-xs text-slate-400 hover:text-slate-600 transition-colors flex items-center gap-1 mt-2"
                                onClick={onRegenerate}
                            >
                                ↺ <span className="underline decoration-slate-300 underline-offset-2">{t('steps.regenerateAudio')}</span>
                            </button>
                        </div>
                    )}

                    {/* Failure Actions */}
                    {progress.status === 'failed' && (
                        <button
                            className="btn btn-danger btn-lg mt-4 w-full rounded-full shadow-lg hover:shadow-xl transition-all"
                            onClick={onRegenerate}
                        >
                            {t('steps.retryAudio')}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
