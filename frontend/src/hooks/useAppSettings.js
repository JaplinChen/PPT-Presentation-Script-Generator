import { useState, useEffect } from 'react';

/**
 * 自動偵測 Ollama URL
 * 如果在 localhost 訪問則返回 localhost:11434
 * 否則使用當前 hostname（例如從手機訪問時）
 */
const getDefaultOllamaUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:11434';

  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:11434';
  }
  return `http://${hostname}:11434`;
};

export const useAppSettings = () => {
  const [showSettings, setShowSettings] = useState(false);
  const [showAvatarSettings, setShowAvatarSettings] = useState(false);
  const [showTTSConfig, setShowTTSConfig] = useState(false);

  const [llmSettings, setLlmSettings] = useState(() => {
    const saved = localStorage.getItem('llmSettings');
    let initialSettings = saved
      ? JSON.parse(saved)
      : {
        defaultProvider: 'gemini',
        providers: {
          gemini: { model: 'gemini-2.0-flash', apiKey: '' },
          openai: { model: '', apiKey: '' },
          openrouter: { model: '', apiKey: '' },
          ollama: { model: '', baseUrl: getDefaultOllamaUrl() }  // 使用動態 URL
        }
      };

    if (initialSettings.providers?.gemini && !initialSettings.providers.gemini.model) {
      initialSettings.providers.gemini.model = 'gemini-2.0-flash';
    }

    // Default to Ollama if no Gemini key and it's currently gemini
    if (initialSettings.defaultProvider === 'gemini' && !initialSettings.providers?.gemini?.apiKey) {
      initialSettings.defaultProvider = 'ollama';
    }

    return initialSettings;
  });

  const [ttsConfig, setTtsConfig] = useState(() => {
    const saved = localStorage.getItem('ttsConfig');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.language && parsed.language.includes('-')) {
        parsed.language = parsed.language.split('-')[0];
      }
      return parsed;
    }
    return {
      language: 'zh',
      voice: 'zh-TW-HsiaoChenNeural',
      rate: '+0%',
      pitch: '+0Hz'
    };
  });

  const [scriptPrompt, setScriptPrompt] = useState(() => {
    return localStorage.getItem('scriptPrompt') || '';
  });

  useEffect(() => {
    localStorage.setItem('llmSettings', JSON.stringify(llmSettings));
  }, [llmSettings]);

  useEffect(() => {
    localStorage.setItem('ttsConfig', JSON.stringify(ttsConfig));
  }, [ttsConfig]);

  useEffect(() => {
    localStorage.setItem('scriptPrompt', scriptPrompt);
  }, [scriptPrompt]);

  return {
    showSettings, setShowSettings,
    showAvatarSettings, setShowAvatarSettings,
    showTTSConfig, setShowTTSConfig,
    llmSettings, setLlmSettings,
    ttsConfig, setTtsConfig,
    scriptPrompt, setScriptPrompt
  };
};
