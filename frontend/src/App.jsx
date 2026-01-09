import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import FileUpload from './components/FileUpload';
import ScriptConfig from './components/ScriptConfig';
import ScriptDisplay from './components/ScriptDisplay';
import SlidePreview from './components/SlidePreview';
import LLMSettingsModal from './components/LLMSettingsModal';
import AvatarSettingsModal from './components/AvatarSettingsModal';
import TTSConfigModal from './components/TTSConfigModal';
import StepIndicator from './components/StepIndicator';
import GenerationStep from './components/GenerationStep';
import LanguageSwitcher from './components/LanguageSwitcher';

import { api } from './services/api';
import { avatarStorage } from './services/avatarStorage';
import { useSession } from './hooks/useSession';
import { useAppSettings } from './hooks/useAppSettings';
import { useGeneration } from './hooks/useGeneration';
import './App.css';
import './App_layout.css';

function App() {
  const { t } = useTranslation();
  const { hasSavedSession, savedSessionData, saveSession, clearSession } = useSession();

  // Custom hooks for complex state
  const {
    showSettings, setShowSettings,
    showAvatarSettings, setShowAvatarSettings,
    showTTSConfig, setShowTTSConfig,
    llmSettings, setLlmSettings,
    ttsConfig, setTtsConfig,
    scriptPrompt, setScriptPrompt
  } = useAppSettings();

  // Basic step and file state
  const [currentStep, setCurrentStep] = useState(1); // 1-6
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [slides, setSlides] = useState(null);
  const [avatarConfig, setAvatarConfig] = useState(null);

  const {
    isGenerating, scriptData, setScriptData,
    generationJobs, setGenerationJobs,
    error, setError,
    handleGenerateScript, resetGeneration
  } = useGeneration(fileId, llmSettings, scriptPrompt);

  // Auto-save Session
  useEffect(() => {
    if (fileId && currentStep > 1) {
      saveSession({
        fileId, currentStep, slides, scriptData, avatarConfig, generationJobs,
        fileMeta: uploadedFile ? { name: uploadedFile.name, size: uploadedFile.size } : null
      });
    }
  }, [fileId, currentStep, slides, scriptData, avatarConfig, generationJobs, uploadedFile, saveSession]);

  const handleResumeSession = () => {
    if (savedSessionData) {
      setFileId(savedSessionData.fileId);
      setCurrentStep(savedSessionData.currentStep);
      setSlides(savedSessionData.slides);
      setScriptData(savedSessionData.scriptData);
      setAvatarConfig(savedSessionData.avatarConfig);
      setGenerationJobs(savedSessionData.generationJobs);
      if (savedSessionData.fileMeta) setUploadedFile(savedSessionData.fileMeta);
      console.log('Session resumed:', savedSessionData.fileId);
    }
  };

  const handleDiscardSession = async () => {
    if (savedSessionData?.fileId) {
      try {
        await api.deleteFile(savedSessionData.fileId);
      } catch (e) {
        console.warn('Failed to cleanup discarded session file:', e);
      }
    }
    clearSession();
    resetGeneration();
  };

  const handleUploadSuccess = async (file, statusData) => {
    clearSession();
    resetGeneration();
    setUploadedFile(file);
    setFileId(statusData.file_id);
    setSlides(statusData.slides);
    setCurrentStep(2);
  };

  const onGenerate = async (config) => {
    try {
      setError(null); // Clear previous errors
      await handleGenerateScript(config);
      setCurrentStep(3);
    } catch (e) {
      console.error('Generation failed:', e);
      setError(e.message || '文稿生成失敗，請重試');
    }
  };

  const handleReset = async () => {
    if (fileId) {
      try { await api.deleteFile(fileId); } catch (e) { console.warn('Reset cleanup failed:', e); }
    }
    clearSession();
    resetGeneration();
    setCurrentStep(1);
    setUploadedFile(null);
    setFileId(null);
    setSlides(null);
    setAvatarConfig(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="container header-container">
          <div className="header-main-row">
            <h1 className="app-title"><span className="title-icon">🎯</span>{t('app.title')}</h1>
            <div className="header-actions">
              <div className="header-capsule">
                <button className={`btn-capsule ${showSettings ? 'active' : ''}`} onClick={() => setShowSettings(!showSettings)} title={t('settings.title')}>⚙️</button>
                <button className={`btn-capsule ${showAvatarSettings ? 'active' : ''}`} onClick={() => setShowAvatarSettings(!showAvatarSettings)} title={t('settings.avatarTitle')}>🎭</button>
                <button className={`btn-capsule ${showTTSConfig ? 'active' : ''}`} onClick={() => setShowTTSConfig(!showTTSConfig)} title={t('settings.ttsTitle')}>🎙️</button>
                <div className="capsule-divider"></div>
                <LanguageSwitcher />
              </div>
            </div>
          </div>
          <p className="app-subtitle">{t('app.subtitle')}</p>
        </div>
      </header>

      {showSettings && (
        <LLMSettingsModal
          onClose={() => setShowSettings(false)}
          onSave={setLlmSettings}
          currentSettings={llmSettings}
          scriptPrompt={scriptPrompt}
          onPromptChange={setScriptPrompt}
        />
      )}
      {showAvatarSettings && (
        <AvatarSettingsModal
          onClose={() => {
            setShowAvatarSettings(false);
            // Refresh config when modal closes
            const settings = avatarStorage.load();

            const defaultPhoto = avatarStorage.getDefaultPhoto();
            if (defaultPhoto || settings.photos.length > 0) {
              // Use default or first photo
              const photoToUse = defaultPhoto || settings.photos[0];
              setAvatarConfig(prev => ({
                ...prev,
                photo_id: photoToUse.photo_id, // Ensure ID is sync
                emotion: settings.preferences.emotion,
                crop_scale: settings.preferences.crop_scale,
                sampling_steps: settings.preferences.sampling_steps
              }));
            }
          }}
        />
      )}
      {showTTSConfig && <TTSConfigModal onClose={() => setShowTTSConfig(false)} onSave={setTtsConfig} currentSettings={ttsConfig} />}

      <main className="app-main container">
        <StepIndicator
          currentStep={currentStep}
          steps={[
            { number: 1, label: t('steps.upload') }, { number: 2, label: t('steps.config') },
            { number: 3, label: t('steps.generateScript') }, { number: 4, label: t('steps.audioGenerate') },
            { number: 5, label: t('steps.pptAssemble') }, { number: 6, label: t('steps.videoEnhance') }
          ]}
        />

        {error && (
          <div className="error-banner" role="alert">
            <span className="error-icon">⚠️</span><span>{error}</span>
            <button onClick={() => setError(null)} className="error-close">×</button>
          </div>
        )}

        {currentStep === 1 && hasSavedSession && (
          <div className="resume-session-banner fade-in">
            <div className="resume-content">
              <span className="icon">🔄</span>
              <div className="text">
                <strong>{t('resume.title')}</strong>
                <span className="meta">
                  {savedSessionData?.fileMeta?.name} ({new Date(savedSessionData?.timestamp).toLocaleString()})
                </span>
                {savedSessionData?.currentStep >= 4 && <span className="status-badge warning">{t('resume.interrupted')}</span>}
              </div>
            </div>
            <div className="resume-actions">
              <button
                onClick={handleDiscardSession}
                title={t('resume.discard')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                </svg>
              </button>
              <button
                onClick={handleResumeSession}
                title={t('resume.restore')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {currentStep === 1 && <div className="step-content"><FileUpload onUploadSuccess={handleUploadSuccess} /></div>}

        {currentStep === 2 && slides && (
          <div className="step-content config-step-layout">
            <div className="config-column">
              <div className="file-summary">
                <h3>檔案：{uploadedFile?.name}</h3>
                <div className="summary-stats">
                  <span>{t('upload.slideCount', { count: slides.length })}</span><span>|</span>
                  <span>{t('upload.titleCount', { count: slides.filter(s => s.title).length })}</span>
                </div>
                <div className="actions-header-row mb-4">
                  <button className="btn btn-secondary-sm" onClick={() => setCurrentStep(1)}>← {t('upload.reupload')}</button>
                </div>
              </div>
              <SlidePreview slides={slides} />
            </div>
            <div className="config-column"><ScriptConfig onGenerate={onGenerate} isGenerating={isGenerating} /></div>
          </div>
        )}

        {currentStep === 3 && scriptData && (
          <div className="step-content">
            <div className="actions-header-row mb-4">
              <button className="btn btn-secondary-sm" onClick={() => setCurrentStep(2)}>{t('action.prevSettings')}</button>
            </div>
            <ScriptDisplay
              scriptData={scriptData}
              slides={slides}
              fileId={fileId}
              onStartNarrated={() => setCurrentStep(4)}
              ttsConfig={ttsConfig}
              onTTSConfigChange={setTtsConfig}
            />
            <div className="actions-footer">
              <button
                className="btn btn-secondary"
                onClick={() => {
                  // Clear previous script data when regenerating
                  setScriptData(null);
                  setError(null);
                  setCurrentStep(2);
                }}
              >
                {t('action.regenerateScript')}
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  const settings = avatarStorage.load();
                  const defaultPhoto = avatarStorage.getDefaultPhoto();
                  if (defaultPhoto) {
                    setAvatarConfig({
                      photo_id: defaultPhoto.photo_id,
                      emotion: settings.preferences.emotion,
                      crop_scale: settings.preferences.crop_scale,
                      sampling_steps: settings.preferences.sampling_steps
                    });
                  }
                  setCurrentStep(4);
                }}
              >{t('action.nextStepAudio')}</button>
            </div>
          </div>
        )}

        {currentStep >= 4 && scriptData && (
          <GenerationStep
            scriptData={scriptData} avatarConfig={avatarConfig}
            onComplete={(res) => { console.log('Generation completed', res); }}
            onError={(err) => setError(typeof err === 'string' ? err : err?.message)}
            initialJobs={generationJobs} onJobsChange={setGenerationJobs}
            activeStep={currentStep} onStepAdvance={() => setCurrentStep(prev => prev + 1)}
            onStepBack={() => setCurrentStep(prev => prev - 1)}
          />
        )}
      </main>

      <footer className="app-footer">
        <div className="container"><p>{t('app.footer')}</p></div>
      </footer>
    </div>
  );
}

export default App;
