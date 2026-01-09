import { API_BASE_URL, fetchWithTimeout } from './config';
export { API_BASE_URL };

export const api = {
    healthCheck: async () => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/health`, { timeout: 5000 });
        return response.json();
    },

    uploadPPT: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetchWithTimeout(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData,
            timeout: 600000 // 10 minutes for large files
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    },

    generateScript: async (fileId, params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/generate/${fileId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 600000 // 10 minutes (extended for retries)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }

        return response.json();
    },

    translateScript: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 120000 // 2 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Translation failed');
        }

        return response.json();
    },

    getFileInfo: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/files/${fileId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch file info');
        }

        return response.json();
    },

    getParseStatus: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/parse/${fileId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch parsing status');
        }
        return response.json();
    },

    deleteFile: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/files/${fileId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete file');
        }

        return response.json();
    },

    getTTSVoices: async (language) => {
        let url = `${API_BASE_URL}/api/tts/voices`;
        if (language) {
            url += `?language=${language}`;
        }
        const response = await fetchWithTimeout(url);
        if (!response.ok) {
            throw new Error('Failed to fetch TTS voices');
        }
        return response.json();
    },

    generateTTSAudio: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 180000 // 3 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'TTS failed');
        }

        return response.json();
    },

    embedVideosToPPT: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/tts/embed-videos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
            timeout: 300000 // 5 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to embed videos to PPT');
        }

        return response.json();
    },

    generateAvatar: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
            timeout: 180000 // 3 minutes, adjust as needed
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate avatar');
        }

        return response.json();
    },

    /**
     * 批量生成數位播報員影片
     * @param {object} params - {photo_id, audio_paths, emotion, ...}
     * @returns {Promise<{job_id: string, status: string}>}
     */
    generateAvatarBatch: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/generate-batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
            timeout: 600000 // 10 minutes, adjust as needed for batch generation
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate batch avatars');
        }

        return response.json();
    },

    generateNarratedPPT: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/ppt/generate-narrated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 900000 // 15 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Narrated PPT generation failed');
        }

        return response.json();
    },

    getPPTJobStatus: async (jobId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/ppt/job/${jobId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch job status');
        }
        return response.json();
    },

    getAvatarJobStatus: async (jobId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/job/${jobId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch avatar job status');
        }
        return response.json();
    },

    generateBatchAudio: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/tts/generate-batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
            timeout: 300000
        });
        return response.json();
    },

    assembleFinalPPT: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/ppt/assemble-final`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
            timeout: 300000
        });
        return response.json();
    },

    // Prompt Management
    listPrompts: async () => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/prompts`);
        if (!response.ok) throw new Error('Failed to list prompts');
        return response.json();
    },

    getPrompt: async (name) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/prompts/${name}`);
        if (!response.ok) throw new Error(`Failed to get prompt ${name}`);
        return response.json(); // { name, content }
    },

    savePrompt: async (name, content) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/prompts/${name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        if (!response.ok) throw new Error(`Failed to save prompt ${name}`);
        return response.json();
    },

    forceUnlock: async () => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/force-unlock`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to force unlock');
        return response.json();
    },

    uploadAvatarPhoto: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/avatar/upload-photo`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Photo upload failed');
        }

        return response.json();
    }
};
