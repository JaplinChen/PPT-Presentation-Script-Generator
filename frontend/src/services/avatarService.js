/**
 * Avatar API Service
 * 
 * 封裝所有與 Avatar 相關的 API 調用
 */
import { API_BASE_URL, fetchWithTimeout } from './config';

/**
 * 取得系統資訊 (GPU 狀態、模型可用性)
 */
export async function getSystemInfo() {
    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/system-info`, { timeout: 30000 }); // 30s timeout for busy GPU
        if (!response.ok) {
            throw new Error('Failed to get system info');
        }
        return response.json();
    } catch (err) {
        console.error('[AvatarService] getSystemInfo failed:', err);
        throw err;
    }
}

/**
 * 上傳播報員照片
 * @param {File} file - 照片檔案
 * @returns {Promise<{photo_id: string, photo_url: string, validation: object}>}
 */
export async function uploadPhoto(file) {

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/upload-photo`, {
        method: 'POST',
        body: formData,
        timeout: 60000 // 60 seconds for validation
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload photo');
    }

    return response.json();
}

/**
 * 生成數位播報員影片
 * @param {object} params - 生成參數
 * @returns {Promise<{job_id: string, status: string}>}
 */
export async function generateAvatar(params) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate avatar');
    }

    return response.json();
}

/**
 * 查詢生成任務狀態
 * @param {string} jobId - 任務 ID
 * @returns {Promise<object>}
 */
export async function getJobStatus(jobId) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/avatar/job/${jobId}/status`);

    if (!response.ok) {
        throw new Error('Failed to get job status');
    }

    return response.json();
}

/**
 * 輪詢任務狀態直到完成
 * @param {string} jobId - 任務 ID
 * @param {function} onProgress - 進度回呼 (progress, message)
 * @param {number} interval - 輪詢間隔 (毫秒)
 * @returns {Promise<object>}
 */
export async function pollJobStatus(jobId, onProgress, interval = 2000) {
    return new Promise((resolve, reject) => {
        const poll = async () => {
            try {
                const status = await getJobStatus(jobId);

                if (onProgress) {
                    onProgress(status.progress, status.message);
                }

                if (status.status === 'completed') {
                    resolve(status);
                } else if (status.status === 'failed') {
                    reject(new Error(status.error || 'Generation failed'));
                } else {
                    // 繼續輪詢
                    setTimeout(poll, interval);
                }
            } catch (error) {
                reject(error);
            }
        };

        poll();
    });
}
