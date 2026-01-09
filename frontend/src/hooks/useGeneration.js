import { useState } from 'react';
import { api } from '../services/api';

export const useGeneration = (fileId, llmSettings, scriptPrompt) => {
    const [isGenerating, setIsGenerating] = useState(false);
    const [scriptData, setScriptData] = useState(null);
    const [generationJobs, setGenerationJobs] = useState(null);
    const [error, setError] = useState(null);

    const handleGenerateScript = async (config) => {
        setError(null);
        setIsGenerating(true);

        try {
            const activeProvider = llmSettings.defaultProvider || 'gemini';
            const providerSettings = llmSettings.providers?.[activeProvider] || { model: '', apiKey: '' };

            const payload = {
                ...config,
                provider: activeProvider,
                model: providerSettings.model || undefined,
                api_key: providerSettings.apiKey || config.api_key,
                ollama_base_url: providerSettings.baseUrl,
                system_prompt: scriptPrompt
            };

            const response = await api.generateScript(fileId, payload);
            const data = { ...response, file_id: fileId };
            setScriptData(data);
            setIsGenerating(false);
            return data;
        } catch (err) {
            setError(err.message);
            setIsGenerating(false);
            throw err;
        }
    };

    const resetGeneration = () => {
        setScriptData(null);
        setGenerationJobs(null);
        setError(null);
        setIsGenerating(false);
    };

    return {
        isGenerating,
        scriptData,
        setScriptData,
        generationJobs,
        setGenerationJobs,
        error,
        setError,
        handleGenerateScript,
        resetGeneration
    };
};
