import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL, api } from '../services/api';

const PROVIDERS = [
  {
    id: 'gemini',
    name: 'Google Gemini',
    sub: 'Google AI Studio / Vertex',
    icon: '🧠',
    models: [
      { value: 'gemini-2.0-flash', label: 'gemini-2.0-flash (Recommended)' },
      { value: 'gemini-1.5-flash', label: 'gemini-1.5-flash' },
      { value: 'gemini-1.5-flash-latest', label: 'gemini-1.5-flash-latest' },
      { value: 'gemini-pro', label: 'gemini-pro' },
    ],
    note: '使用 GOOGLE GEMINI API KEY，無需 base URL。'
  },
  {
    id: 'openai',
    name: 'OpenAI',
    sub: '標準雲端 API',
    icon: '🌐',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
    note: '使用 OPENAI_API_KEY，預設 base: api.openai.com。'
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    sub: '多模型聚合',
    icon: '🛰️',
    models: ['meta-llama/llama-3.1-8b-instruct', 'anthropic/claude-3.5-sonnet', 'gpt-4o-mini'],
    note: '需 OPENROUTER_API_KEY，預設 base: https://openrouter.ai/api/v1'
  },
  {
    id: 'ollama',
    name: 'Ollama',
    sub: '本地 Llama / Mistral',
    icon: '🦙',
    models: [],
    note: '本地端運行，預設港口 11434。'
  }
];

/**
 * 自動偵測 Ollama URL（與 useAppSettings 保持一致）
 */
const getDefaultOllamaUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:11434';

  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:11434';
  }
  return `http://${hostname}:11434`;
};

const DEFAULT_SETTINGS = {
  defaultProvider: 'gemini',
  providers: {
    gemini: { model: '', apiKey: '' },
    openai: { model: '', apiKey: '' },
    openrouter: { model: '', apiKey: '' },
    ollama: { model: '', baseUrl: getDefaultOllamaUrl() }  // 使用動態 URL
  }
};

function LLMSettingsModal({ onClose, onSave, currentSettings, scriptPrompt, onPromptChange }) {
  const { t } = useTranslation();
  const initial = currentSettings || DEFAULT_SETTINGS;
  const [activeTab, setActiveTab] = useState('providers'); // 'providers' | 'prompt'
  const [activeProvider, setActiveProvider] = useState(initial.defaultProvider || 'gemini');
  const [defaultProvider, setDefaultProvider] = useState(initial.defaultProvider || 'gemini');
  const [settings, setSettings] = useState(() => initial);
  const [showKey, setShowKey] = useState(false);

  // Dynamic models state
  const [availableModels, setAvailableModels] = useState(null);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [fetchError, setFetchError] = useState(null);

  // Prompt state
  const [localPrompt, setLocalPrompt] = useState('');
  const [promptList, setPromptList] = useState([]);
  const [selectedPromptFile, setSelectedPromptFile] = useState('system');
  const [isLoadingPrompt, setIsLoadingPrompt] = useState(false);
  const [promptSaveStatus, setPromptSaveStatus] = useState('');

  // Sync if props change
  useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings);
    }
  }, [currentSettings]);

  const currentProvider = useMemo(
    () => PROVIDERS.find((p) => p.id === activeProvider) || PROVIDERS[0],
    [activeProvider]
  );

  const providerState = settings.providers?.[activeProvider] ?? { model: '', apiKey: '' };

  const updateProviderState = useCallback((fields) => {
    setSettings(prev => ({
      ...prev,
      providers: {
        ...prev.providers,
        [activeProvider]: {
          ...(prev.providers?.[activeProvider] ?? {}),
          ...fields
        }
      }
    }));
  }, [activeProvider]);

  // Fetch prompt list (memoized)
  const fetchPromptList = useCallback(async () => {
    try {
      const list = await api.listPrompts();
      setPromptList(list);
      if (list.includes('system')) {
        setSelectedPromptFile('system');
      } else if (list.length > 0) {
        setSelectedPromptFile(list[0]);
      }
    } catch (e) {
      console.error("Failed to list prompts", e);
    }
  }, []);

  // Fetch prompt content (memoized)
  const fetchPromptContent = useCallback(async (name) => {
    setIsLoadingPrompt(true);
    try {
      const data = await api.getPrompt(name);
      setLocalPrompt(data.content);
    } catch (e) {
      console.error(`Failed to load prompt ${name}`, e);
      setLocalPrompt("");
    } finally {
      setIsLoadingPrompt(false);
    }
  }, []);

  // 1. Fetch prompt list on tab switch
  useEffect(() => {
    if (activeTab === 'prompt') {
      fetchPromptList();
    }
  }, [activeTab, fetchPromptList]);

  // 2. Fetch specific prompt content when file selection changes
  useEffect(() => {
    if (activeTab === 'prompt' && selectedPromptFile) {
      fetchPromptContent(selectedPromptFile);
    }
  }, [activeTab, selectedPromptFile, fetchPromptContent]);

  const handleResetPrompt = useCallback(async () => {
    if (selectedPromptFile) {
      fetchPromptContent(selectedPromptFile);
    }
  }, [selectedPromptFile, fetchPromptContent]);

  // Fetch available models for Gemini (with AbortController support)
  const fetchGeminiModels = useCallback(async (key, signal) => {
    setIsLoadingModels(true);
    setFetchError(null);
    try {
      const url = new URL(`${API_BASE_URL}/api/gemini/models`, window.location.origin);
      if (key) url.searchParams.append('api_key', key);

      const res = await fetch(url, { signal });
      const data = await res.json();

      if (data.success === false) {
        throw new Error(data.error || 'Failed to fetch models');
      }

      if (data.models && Array.isArray(data.models)) {
        setAvailableModels(data.models);
      }
    } catch (err) {
      if (err.name === 'AbortError') return; // Ignore abort errors
      console.error("Error fetching models:", err);
      setFetchError(err.message);
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Fetch available models for Ollama (with AbortController support)
  const fetchOllamaModels = useCallback(async (baseUrl, signal) => {
    setIsLoadingModels(true);
    setFetchError(null);
    try {
      const url = new URL(`${API_BASE_URL}/api/ollama/models`, window.location.origin);
      if (baseUrl) url.searchParams.append('base_url', baseUrl);

      const res = await fetch(url, { signal });
      const data = await res.json();

      if (data.success === false) {
        throw new Error(data.error || 'Failed to fetch Ollama models');
      }

      if (data.models && Array.isArray(data.models)) {
        setAvailableModels(data.models);

        // Auto-select first model if current one is empty or not in the list
        const currentModel = providerState.model;
        const modelNames = data.models.map(m => m.value);

        if (!currentModel || !modelNames.includes(currentModel)) {
          if (data.models.length > 0) {
            const firstModel = data.models[0].value;
            updateProviderState({ model: firstModel });
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return; // Ignore abort errors
      console.error("Error fetching Ollama models:", err);
      setFetchError(err.message);
    } finally {
      setIsLoadingModels(false);
    }
  }, [providerState.model, updateProviderState]);

  // Auto-fetch when provider or relevant config changes (debounced with AbortController)
  useEffect(() => {
    const controller = new AbortController();

    const timer = setTimeout(() => {
      if (activeProvider === 'gemini') {
        fetchGeminiModels(providerState.apiKey, controller.signal);
      } else if (activeProvider === 'ollama') {
        fetchOllamaModels(providerState.baseUrl, controller.signal);
      } else {
        setAvailableModels(null);
        setFetchError(null);
      }
    }, 800); // 800ms debounce

    return () => {
      clearTimeout(timer);
      controller.abort(); // Cancel pending requests on cleanup
    };
  }, [activeProvider, providerState.apiKey, providerState.baseUrl, fetchGeminiModels, fetchOllamaModels]);


  const handleSave = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const payload = {
      ...settings,
      defaultProvider: defaultProvider || settings.defaultProvider || activeProvider
    };

    // Save LLM settings
    if (onSave) onSave(payload);

    // Save Prompt (to Backend)
    if (activeTab === 'prompt' && selectedPromptFile) {
      setPromptSaveStatus('Saving...');
      try {
        await api.savePrompt(selectedPromptFile, localPrompt);
        // Specifically for 'system' prompt, we ideally also update the local state if used by frontend
        // But since our implementation plan moves source of truth to backend, 
        // the 'onPromptChange' prop might become deprecated or only used for session overrides.
        // For now, if we are editing 'system', we also push to onPromptChange to keep existing flow working 
        // until we fully refactor useGeneration to pull from backend every time (or rely on backend default).
        if (selectedPromptFile === 'system' && onPromptChange) {
          onPromptChange(localPrompt);
        }
        setPromptSaveStatus('Saved!');
        setTimeout(() => setPromptSaveStatus(''), 2000);
      } catch (e) {
        console.error("Failed to save prompt", e);
        setPromptSaveStatus('Error!');
      }
    }

    if (onClose) onClose();
  };

  // Determine which models to show: dynamic or static
  const hasDynamicModels = (activeProvider === 'gemini' || activeProvider === 'ollama') && availableModels && availableModels.length > 0;
  const displayedModels = hasDynamicModels ? availableModels : currentProvider.models;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="settings-shell">
          <aside className="settings-sidebar">
            <h4 className="sidebar-title">SETTINGS</h4>

            <div className="sidebar-tabs">
              <button
                className={`sidebar-tab ${activeTab === 'providers' ? 'active' : ''}`}
                onClick={() => setActiveTab('providers')}
              >
                📡 {t('settings.llmProviders')}
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'prompt' ? 'active' : ''}`}
                onClick={() => setActiveTab('prompt')}
              >
                📝 {t('settings.promptSettings')}
              </button>
            </div>

            {activeTab === 'providers' && (
              <div className="sidebar-list">
                {PROVIDERS.map((p) => (
                  <button
                    key={p.id}
                    className={`sidebar-item ${activeProvider === p.id ? 'active' : ''}`}
                    onClick={() => setActiveProvider(p.id)}
                  >
                    <span className="sidebar-icon" aria-hidden="true">
                      {p.icon}
                    </span>
                    <div className="sidebar-text">
                      <div className="sidebar-name">{p.name}</div>
                      <div className="sidebar-sub">{t(`settings.providerSub.${p.id}`)}</div>
                    </div>
                    {defaultProvider === p.id && <span className="default-badge" title={t('settings.default')}>✓</span>}
                  </button>
                ))}
              </div>
            )}

            {activeTab === 'prompt' && (
              <div className="sidebar-list">
                <div className="p-3 text-sm text-gray-500">
                  {t('settings.editPromptDesc')}
                </div>
              </div>
            )}

            <div className="sidebar-footer">v2.5.0</div>
          </aside>

          <div className="settings-main">
            <div className="modal-header fancy">
              <div className="flex-1 min-w-0">
                {activeTab === 'providers' ? (
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-xl font-bold text-gray-900 m-0">{currentProvider.name} {t('settings.providerConfig')}</h3>
                      {defaultProvider === currentProvider.id ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {t('settings.defaultProvider')}
                        </span>
                      ) : null}
                    </div>
                  </div>
                ) : (
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 m-0">{t('settings.systemPrompt')}</h3>
                    <p className="text-sm text-gray-500">{t('settings.systemPromptDesc')}</p>
                  </div>
                )}
              </div>

              <div className="header-actions flex-shrink-0 ml-4 flex items-center gap-2">
                {activeTab === 'providers' ? (
                  <>
                    <button
                      className="icon-btn-ghost"
                      onClick={() => setDefaultProvider(activeProvider)}
                      title={defaultProvider === activeProvider ? t('settings.currentDefault') : t('settings.setDefaultProvider')}
                    >
                      {defaultProvider === activeProvider ? '⭐' : '☆'}
                    </button>
                    <div className="w-px h-4 bg-gray-300 mx-1"></div>
                    <button className="btn-icon-action" onClick={onClose} type="button" title={t('settings.cancelClose')}>
                      ✕
                    </button>
                    <button className="btn-icon-action text-primary border-primary" onClick={handleSave} type="button" title={t('settings.saveSettings')}>
                      ✓
                    </button>
                  </>
                ) : (
                  <>
                    <span className="text-xs text-green-600 mr-2">{promptSaveStatus}</span>
                    <button
                      className="ghost-btn w-11 h-11 p-2.5"
                      onClick={handleResetPrompt}
                      title={t('settings.resetPrompt')}
                    >
                      ↺
                    </button>
                    <button className="btn-icon-action" onClick={onClose} type="button" title={t('action.close')}>
                      ✕
                    </button>
                    <button className="btn-icon-action text-primary border-primary" onClick={handleSave} type="button" title={t('settings.savePrompt')}>
                      💾
                    </button>
                  </>
                )}
              </div>
            </div>

            <form onSubmit={handleSave} className="flex flex-col flex-1 w-full overflow-hidden" noValidate>
              <div className="flex-1 w-full overflow-y-auto p-4">
                {activeTab === 'providers' ? (
                  <>
                    {activeProvider !== 'ollama' && (
                      <div className="config-field compact">
                        <label>{t('settings.apiKey')}</label>
                        <div className="flex gap-2 max-w-lg">
                          <input
                            type={showKey ? 'text' : 'password'}
                            value={providerState.apiKey}
                            onChange={(e) => updateProviderState({ apiKey: e.target.value })}
                            placeholder={t('settings.apiKeyPlaceholder')}
                            autoComplete="username current-password"
                            name="apiKey"
                            className="flex-1"
                          />
                          <button className="btn-icon-action" onClick={() => setShowKey(!showKey)} type="button" title={showKey ? t('settings.hideApiKey') : t('settings.showApiKey')}>
                            {showKey ? '🙈' : '👁️'}
                          </button>
                        </div>
                        <p className="hint">{t('settings.apiKeyHint')}</p>
                      </div>
                    )}

                    {activeProvider === 'ollama' && (
                      <div className="config-field compact">
                        <label>{t('settings.baseUrl')}</label>
                        <input
                          type="text"
                          value={providerState.baseUrl || ''}
                          onChange={(e) => updateProviderState({ baseUrl: e.target.value })}
                          placeholder="http://localhost:11434"
                          className="max-w-lg"
                        />
                        <p className="hint">{t('settings.ollamaHint')}</p>
                      </div>
                    )}

                    <div className="config-field compact">
                      <div className="flex justify-between items-center mb-1">
                        <label className="mb-0">{t('settings.model')}</label>
                        {(activeProvider === 'gemini' || activeProvider === 'ollama') && (
                          <div className="flex items-center gap-2">
                            {isLoadingModels && <span className="text-xs text-gray-500 loading-pulse">{t('settings.updatingModels')}</span>}
                            {fetchError && <span className="text-xs text-red-400" title={fetchError}>{t('settings.fetchError') || '更新失敗'}</span>}
                            <button
                              className="text-xs text-primary hover:underline"
                              onClick={(e) => {
                                e.preventDefault();
                                if (activeProvider === 'gemini') fetchModels(providerState.apiKey);
                                else if (activeProvider === 'ollama') fetchOllamaModels(providerState.baseUrl);
                              }}
                              disabled={isLoadingModels}
                              type="button"
                            >
                              {t('settings.refreshModels')}
                            </button>

                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <select
                          value={
                            providerState.model ||
                            (typeof displayedModels[0] === 'string'
                              ? displayedModels[0]
                              : displayedModels[0]?.value)
                          }
                          onChange={(e) => updateProviderState({ model: e.target.value })}
                          disabled={isLoadingModels && (!displayedModels || displayedModels.length === 0)}
                        >
                          {isLoadingModels && <option value="">{t('settings.fetchingModels')}</option>}
                          {!isLoadingModels && displayedModels.length === 0 && <option value="">{t('settings.noModels')}</option>}
                          {displayedModels.map((m) => {
                            const value = typeof m === 'string' ? m : m.value;
                            const label = typeof m === 'string' ? m : m.label;
                            return (
                              <option key={value} value={value}>
                                {label}
                              </option>
                            );
                          })}
                        </select>
                        <input
                          type="text"
                          className="flex-1"
                          placeholder={t('settings.customModel')}
                          value={providerState.model}
                          onChange={(e) => updateProviderState({ model: e.target.value })}
                        />
                      </div>
                      <p className="hint">{t(`settings.providerNote.${activeProvider}`)}</p>
                    </div>
                  </>
                ) : (
                  <div className="prompt-editor-container">
                    <div className="config-field w-full">
                      <div className="prompt-selector-row flex items-center gap-4 mb-4">
                        <label className="prompt-selector-label whitespace-nowrap shrink-0">{t('settings.selectPrompt')}</label>
                        <select
                          value={selectedPromptFile}
                          onChange={(e) => setSelectedPromptFile(e.target.value)}
                          className="prompt-template-select"
                        >
                          {(() => {
                            const getOrder = (p) => {
                              const order = ['system', 'opening', 'slide', 'transition', 'qa', 'rewrite', 'multiversion_opening', 'audio', 'video'];
                              return order.indexOf(p) >= 0 ? order.indexOf(p) : 99;
                            };

                            return [...promptList]
                              .sort((a, b) => getOrder(a) - getOrder(b))
                              .map(p => (
                                <option key={p} value={p}>{t(`settings.promptTemplates.${p}`) || p}</option>
                              ));
                          })()}
                        </select>
                      </div>

                      <textarea
                        className="prompt-textarea"
                        value={localPrompt}
                        onChange={(e) => setLocalPrompt(e.target.value)}
                        placeholder={isLoadingPrompt ? t('settings.loading') : t('settings.promptPlaceholder')}
                        rows={16}
                        spellCheck="false"
                        disabled={isLoadingPrompt}
                      />
                    </div>

                    <div className="placeholder-helper">
                      <h5>{t('settings.placeholders')}:</h5>
                      <div className="placeholder-grid">
                        <code>{'{language}'}</code> <span>{t('settings.promptVars.language')}</span>
                        <code>{'{tone}'}</code> <span>{t('settings.promptVars.tone')}</span>
                        <code>{'{min_length}'}</code> <span>{t('settings.promptVars.minLength')}</span>
                        <code>{'{total_slides}'}</code> <span>{t('settings.promptVars.totalSlides')}</span>
                        <code>{'{int_avg_time_per_slide}'}</code> <span>{t('settings.promptVars.avgTime')}</span>
                        <code>{'{avatar_name_display}'}</code> <span>{t('settings.promptVars.avatarName')}</span>
                      </div>
                      <p className="text-xs mt-2 text-gray-500">※ {t('settings.placeholderNote')}</p>
                    </div>
                  </div>
                )}

              </div>

            </form>
          </div>
        </div>
      </div>
    </div>

  );
}

export default LLMSettingsModal;
