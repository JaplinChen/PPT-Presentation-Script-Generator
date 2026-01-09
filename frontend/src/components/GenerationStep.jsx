import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';
import './GenerationStep.css';

import StepAudioGeneration from './steps/StepAudioGeneration';
import StepAvatarGeneration from './steps/StepAvatarGeneration';
import StepFinalAssembly from './steps/StepFinalAssembly';

export default function GenerationStep({
    scriptData,
    avatarConfig,
    onComplete,
    onError,
    initialJobs,
    onJobsChange,
    activeStep,
    onStepAdvance,
    onStepBack
}) {
    const { t } = useTranslation();
    const fileId = scriptData?.file_id;
    const ttsConfig = JSON.parse(localStorage.getItem('ttsConfig') || '{}');

    // 用於追蹤哪些步驟已經自動跳轉過，防止在「回上一步」後又被自動推向下一步
    const autoAdvancedSteps = useRef({ 4: false, 5: false });

    // 狀態管理：任務 ID
    const [jobs, setJobs] = useState(initialJobs || {
        audio: null,
        avatar: null,
        assemble: null
    });

    // 包裝 setJobs，狀態同步改由 useEffect 處理
    const updateJobs = (updates) => {
        setJobs(prev => {
            return typeof updates === 'function' ? updates(prev) : updates;
        });
    };

    // 監聽 jobs 變更並同步到父層
    useEffect(() => {
        if (onJobsChange) {
            onJobsChange(jobs);
        }
    }, [jobs, onJobsChange]);

    // 狀態管理：進度與訊息
    const [progress, setProgress] = useState({
        audio: { status: 'idle', progress: 0, message: '', result: null },
        avatar: { status: 'idle', progress: 0, message: '', result: null },
        assemble: { status: 'idle', progress: 0, message: '', result: null }
    });

    // 追蹤各步驟是否已由使用者點擊開始
    const [startedSteps, setStartedSteps] = useState({
        audio: !!jobs.audio,
        avatar: !!jobs.avatar,
        assemble: !!jobs.assemble
    });

    // 步驟特定參數 (如預覽模式)
    const [stepOptions, setStepOptions] = useState({
        avatar: {}
    });

    const [generating, setGenerating] = useState(true); // 永遠設為 true，因為我們現在透過進度區域內部控制

    // 啟動特定步驟
    const startStep = (type, options = {}) => {
        setStepOptions(prev => ({ ...prev, [type]: options }));
        setStartedSteps(prev => ({ ...prev, [type]: true }));
    };

    // 6. 專屬狀態：是否為 Step 6 發起的 PPT Update (防止誤判 Step 5 的完成狀態)
    const [isStep6Assemble, setIsStep6Assemble] = useState(false);

    // 重新生成邏輯 (支援級聯清除)
    const handleRegenerate = (type) => {
        if (type === 'audio') {
            // 清除 4, 5, 6
            updateJobs(prev => ({ ...prev, audio: null, avatar: null, assemble: null }));
            setProgress(prev => ({
                ...prev,
                audio: { status: 'idle', progress: 0, message: '', result: null },
                avatar: { status: 'idle', progress: 0, message: '', result: null },
                assemble: { status: 'idle', progress: 0, message: '', result: null }
            }));
            setStartedSteps(prev => ({ ...prev, audio: false, avatar: false, assemble: false }));
            setIsStep6Assemble(false);
            autoAdvancedSteps.current[4] = false;
            autoAdvancedSteps.current[5] = false;
        } else if (type === 'avatar') {
            // 清除 5, 6
            updateJobs(prev => ({ ...prev, avatar: null, assemble: null }));
            setProgress(prev => ({
                ...prev,
                avatar: { status: 'idle', progress: 0, message: '', result: null },
                assemble: { status: 'idle', progress: 0, message: '', result: null }
            }));
            setStartedSteps(prev => ({ ...prev, avatar: false, assemble: false }));
            setIsStep6Assemble(false);
            autoAdvancedSteps.current[5] = false;
        } else if (type === 'assemble') {
            // 僅清除 6
            updateJobs(prev => ({ ...prev, assemble: null }));
            setProgress(prev => ({
                ...prev,
                assemble: { status: 'idle', progress: 0, message: '', result: null }
            }));
            setStartedSteps(prev => ({ ...prev, assemble: false }));
            setIsStep6Assemble(false);
        }
    };

    // 0. 觸發 Audio (Step 4)
    useEffect(() => {
        if (activeStep === 4 && !jobs.audio && startedSteps.audio) {
            const startAudio = async () => {
                try {
                    const result = await api.generateBatchAudio({
                        slide_scripts: scriptData.slide_scripts,
                        voice: ttsConfig.voice || 'zh-TW-HsiaoChenNeural',
                        rate: ttsConfig.rate || '+0%',
                        pitch: ttsConfig.pitch || '+0Hz'
                    });
                    updateJobs(prev => ({ ...prev, audio: result.job_id }));
                } catch (err) {
                    onError(`語音生成失敗: ${err.message}`);
                    setStartedSteps(prev => ({ ...prev, audio: false }));
                }
            };
            startAudio();
        }
    }, [activeStep, jobs.audio, startedSteps.audio, scriptData, ttsConfig, onError]);

    // 1. 輪詢 Audio (Step 4)
    useEffect(() => {
        let active = true;
        const currentJobId = jobs.audio;
        if (!currentJobId) return;

        // console.log(`[Polling] Started Audio poll for: ${currentJobId}`);

        const poll = async () => {
            try {
                const status = await api.getPPTJobStatus(currentJobId);

                if (!active || jobs.audio !== currentJobId) {
                    // console.log(`[Polling] Stale Audio poll stopped for: ${currentJobId}`);
                    return;
                }

                setProgress(prev => ({ ...prev, audio: status }));

                if (status.status === 'completed') {
                    // console.log(`[Polling] Audio Job ${currentJobId} completed!`);
                    if (activeStep === 4 && !autoAdvancedSteps.current[4]) {
                        // autoAdvancedSteps.current[4] = true;
                        // onStepAdvance(); // Disable auto-advance to allow user to regenerate or continue manually
                    }
                } else if (status.status === 'failed') {
                    console.error(`[Polling] Audio Job ${currentJobId} failed:`, status.error);
                    onError(status.error || status.message);
                } else {
                    setTimeout(() => { if (active) poll(); }, 2000);
                }
            } catch (err) {
                if (active) onError(err.message);
            }
        };
        poll();
        return () => { active = false; };
    }, [jobs.audio, activeStep, onStepAdvance, onError]);

    // 2. 觸發 Assemble (Step 5 - Now triggered after Audio)
    useEffect(() => {
        // Condition: Step 5 active, not started, Audio done.
        // Even if no avatar video, we can distinct this step.
        if (activeStep === 5 && !jobs.assemble && startedSteps.assemble && progress.audio.status === 'completed') {
            const audioFiles = progress.audio.result?.audio_files;
            if (!audioFiles || audioFiles.length === 0) return;

            // Step 5 only uses static image (photo_id) initially
            // Video paths are empty at this stage
            const videoPaths = [];

            api.assembleFinalPPT({
                file_id: fileId,
                slide_scripts: scriptData.slide_scripts,
                audio_paths: audioFiles, // Audio is ready
                video_paths: videoPaths, // No video yet
                voice: ttsConfig.voice,
                photo_id: avatarConfig?.photo_id // Pass photo for static image layout
            }).then(res => {
                updateJobs(prev => ({ ...prev, assemble: res.job_id }));
            }).catch(err => {
                onError(`封裝失敗: ${err.message}`);
                setStartedSteps(prev => ({ ...prev, assemble: false }));
            });
        }
    }, [activeStep, jobs.assemble, startedSteps.assemble, progress.audio.status, progress.audio.result, fileId, scriptData, ttsConfig, onError, avatarConfig]);

    // 3. 輪詢 Assemble (Step 5)
    useEffect(() => {
        let active = true;
        const currentJobId = jobs.assemble;
        if (!currentJobId) return;

        const poll = async () => {
            try {
                const status = await api.getPPTJobStatus(currentJobId);
                if (!active || jobs.assemble !== currentJobId) return;

                setProgress(prev => ({ ...prev, assemble: status }));

                if (status.status === 'completed') {
                    // Update final result for download even at this stage
                    if (status.result) {
                        onComplete({ ppt: status.result });
                    }

                    if (activeStep === 5 && !autoAdvancedSteps.current[5]) {
                        // Optional: Auto advance to Avatar Video step? 
                        // Or let user decide. Let's not auto-advance to keep user in control.
                    }
                } else if (status.status === 'failed') {
                    onError(status.error || status.message);
                } else {
                    setTimeout(() => { if (active) poll(); }, 2000);
                }
            } catch (err) {
                if (active) onError(err.message);
            }
        };
        poll();
        return () => { active = false; };
    }, [jobs.assemble, onComplete, onError, activeStep]);


    // 4. 觸發 Avatar (Step 6 - Optional Enhancement)
    useEffect(() => {
        if (activeStep === 6 && !jobs.avatar && startedSteps.avatar && progress.audio.status === 'completed') {
            const audioFiles = progress.audio.result?.audio_files;

            if (avatarConfig) {
                if (!audioFiles || !Array.isArray(audioFiles) || audioFiles.length === 0) {
                    console.warn("Avatar trigger BLOCKED: audio_files is empty.");
                    return;
                }

                api.generateAvatarBatch({
                    photo_id: avatarConfig.photo_id,
                    audio_paths: audioFiles,
                    emotion: avatarConfig.emotion,
                    crop_scale: avatarConfig.crop_scale,
                    sampling_steps: avatarConfig.sampling_steps,
                    max_size: avatarConfig.max_size || 480,
                    ...stepOptions.avatar
                }).then(res => {
                    updateJobs(prev => ({ ...prev, avatar: res.job_id }));
                }).catch(err => {
                    onError(`播報員生成失敗: ${err.message}`);
                    setStartedSteps(prev => ({ ...prev, avatar: false }));
                });
            } else {
                // No config, cannot generate video
                onError("未設定播報員，無法生成影片");
                setStartedSteps(prev => ({ ...prev, avatar: false }));
            }
        }
    }, [activeStep, jobs.avatar, startedSteps.avatar, progress.audio.status, avatarConfig, progress.audio.result, onError, stepOptions.avatar]);

    // 5. 輪詢 Avatar (Step 6) AND Re-Assemble Logic
    useEffect(() => {
        let active = true;
        const currentJobId = jobs.avatar;
        if (!currentJobId) return;

        const poll = async () => {
            try {
                const status = await api.getAvatarJobStatus(currentJobId);
                if (!active || jobs.avatar !== currentJobId) return;

                setProgress(prev => ({ ...prev, avatar: status }));

                if (status.status === 'completed') {
                    // Avatar Video Done! Now we must re-assemble PPT with videos.
                    // Trigger a silent re-assembly or notify user?
                    // Let's trigger a second assembly job automatically to update the PPT.

                    // We need a way to trigger assembly again. 
                    // Since 'jobs.assemble' is already set from Step 5, we might need to reset it or create a new job?
                    // A cleaner way is to let the user click "Update PPT" or just handle it here.
                    // To keep it simple: We won't auto-re-assemble inside this hook to avoid complexity looping.
                    // The UI component for Step 6 will handle the "Finalize with Video" action (which calls assemble again).

                } else if (status.status === 'failed') {
                    onError(status.error || status.message);
                } else {
                    setTimeout(() => { if (active) poll(); }, 2000);
                }
            } catch (err) {
                if (!active) return;
                onError(`播報員狀態更新失敗: ${err.message}`);
            }
        };
        poll();
        return () => { active = false; };
    }, [jobs.avatar, onError]);

    const handleStepBackWithLogic = () => {
        // 如果從 Step 5 (PPT 製作) 返回 Step 4，自動重置 Step 5 的狀態
        // 這樣再次進入時可以確保重新製作，避免顯示舊的結果，且確保套用最新的播報員設定
        if (activeStep === 5) {
            handleRegenerate('assemble');
        }
        onStepBack();
    };

    return (
        <div className="generation-step">
            <div className="glass-card">
                <div className="card-header-actions mb-4">
                    <button className="btn btn-secondary-sm" onClick={handleStepBackWithLogic}>← {t('action.back', '上一步')}</button>
                    <div className="step-badge">
                        Step {activeStep}: {activeStep === 4 ? t('steps.audioGenerate') : activeStep === 5 ? t('steps.pptAssemble') : t('steps.videoEnhance')}
                    </div>
                </div>

                <div className="generation-stages-container">
                    {/* 1. 語音進度 (Step 4) */}
                    {activeStep === 4 && (
                        <StepAudioGeneration
                            scriptData={scriptData}
                            started={startedSteps.audio}
                            progress={progress.audio}
                            onStart={() => startStep('audio')}
                            onRegenerate={() => handleRegenerate('audio')}
                            onNext={onStepAdvance}
                        />
                    )}

                    {/* 2. 封裝進度 (Step 5 - Now Initial Assembly) */}
                    {activeStep === 5 && (
                        <StepFinalAssembly
                            scriptData={scriptData}
                            avatarConfig={avatarConfig}
                            started={startedSteps.assemble}
                            progress={progress.assemble}
                            onStart={() => startStep('assemble')}
                            onRegenerate={() => handleRegenerate('assemble')}
                            onNext={onStepAdvance}
                        />
                    )}

                    {/* 3. 播報員進度 (Step 6 - Now Optional Video Enhancement) */}
                    {activeStep === 6 && (
                        <div className="step-6-container">
                            <StepAvatarGeneration
                                avatarConfig={avatarConfig}
                                started={startedSteps.avatar}
                                progress={progress.avatar}
                                audioCompleted={progress.audio.status === 'completed'}
                                onStart={() => startStep('avatar')}
                                onPreview={() => startStep('avatar', { preview_duration: 5.0 })}
                                onRegenerate={() => handleRegenerate('avatar')} // This will clear avatar job
                                onNext={() => {
                                    // Special "Update PPT" Manual Trigger for Hybrid Workflow
                                    // Because videos might be generated externally (Colab), we cannot rely solely on internal state.
                                    // We infer expected video paths based on audio files.
                                    const audioFiles = progress.audio.result?.audio_files;

                                    // Infer video paths: replace .mp3 with .mp4
                                    // The backend will check if these files actually exist.
                                    let videoPaths = [];
                                    if (audioFiles && audioFiles.length > 0) {
                                        videoPaths = audioFiles.map(path => path.replace('.mp3', '.mp4'));
                                    } else if (progress.avatar.result?.video_files) {
                                        // Fallback to internal result if available
                                        videoPaths = progress.avatar.result.video_files;
                                    }

                                    if (videoPaths.length === 0) {
                                        alert("⚠️ 找不到音訊檔，無法推斷影片路徑。請先完成語音生成。");
                                        return;
                                    }

                                    // UI Feedback
                                    alert(`🚀 開始封裝 PPT...\n\n系統將嘗試搜尋以下影片:\n${videoPaths.length} 個檔案 (.mp4)\n\n請稍候，完成後會自動通知。`);

                                    setIsStep6Assemble(true); // Mark this as a Step 6 initiated update

                                    // Re-trigger assembly with inferred videos
                                    api.assembleFinalPPT({
                                        file_id: fileId,
                                        slide_scripts: scriptData.slide_scripts,
                                        audio_paths: audioFiles,
                                        video_paths: videoPaths,
                                        voice: ttsConfig.voice,
                                        photo_id: avatarConfig?.photo_id
                                    }).then(res => {
                                        updateJobs(prev => ({ ...prev, assemble: res.job_id }));
                                        // Optionally, scroll to top or show a loading indicator
                                    }).catch(err => {
                                        alert(`❌ 啟動封裝失敗: ${err.message}`);
                                    });
                                }}
                            />

                            {/* Show Assembly Progress Overlay or Status */}
                            {jobs.assemble && isStep6Assemble && progress.assemble.status === 'processing' && (
                                <div className="mt-4 p-4 bg-gray-900 border border-yellow-500 rounded text-yellow-300">
                                    <span className="animate-pulse">🔄 正在重新封裝 PPT 中...</span>
                                    <span className="ml-2 font-mono">{progress.assemble.progress}%</span>
                                </div>
                            )}
                            {jobs.assemble && isStep6Assemble && progress.assemble.status === 'completed' && (
                                <div className="mt-4 p-4 bg-green-900 border border-green-500 rounded text-green-300">
                                    <p>✅ PPT 更新完成！已自動下載。</p>
                                    {/* Hidden auto-download trigger */}
                                    {progress.assemble.result?.url_path && (
                                        <a
                                            href={`${api.API_BASE_URL || ''}${progress.assemble.result.url_path}`}
                                            download
                                            style={{ display: 'none' }}
                                            ref={(link) => {
                                                if (link && !link.dataset.autoClicked) {
                                                    link.dataset.autoClicked = "true";
                                                    link.click();
                                                }
                                            }}
                                        />
                                    )}
                                </div>
                            )}

                            {/* Render Assembly Progress here too if re-assembling? */}
                            {/* Simplified: The user generates video, then clicks "Finish" or "Update PPT" */}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
