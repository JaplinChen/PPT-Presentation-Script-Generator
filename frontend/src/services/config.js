/**
 * API Configuration and Shared Utilities
 */

// Use empty string to default to same origin (Vite proxy will handle it)
// This enables LAN access without manual IP config
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch wrapper with timeout support
 * @param {string} resource - URL or Request object
 * @param {object} options - Fetch options with optional 'timeout' (default 30s)
 */
export const fetchWithTimeout = async (resource, options = {}) => {
    const { timeout = 30000, ...rest } = options;

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(resource, {
            ...rest,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        if (error.name === 'AbortError') {
            throw new Error(`Request timed out (${timeout}ms). Please check backend availability or network.`);
        }
        throw error;
    }
};
