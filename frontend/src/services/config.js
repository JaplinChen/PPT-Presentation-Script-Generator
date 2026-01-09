/**
 * API Configuration and Shared Utilities
 */

// Use empty string to default to same origin (Vite proxy will handle it)
// This enables LAN access without manual IP config
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Gets the full backend URL for resource access (downloads, static files)
 * This is needed for cross-computer access where relative URLs don't work.
 * 
 * @param {string} path - The path like /outputs/file.pptx
 * @returns {string} Full URL with proper host
 */
export const getBackendUrl = (path) => {
    // If API_BASE_URL is set explicitly, use it
    if (API_BASE_URL) {
        return `${API_BASE_URL}${path}`;
    }

    // For cross-computer access: construct URL using current hostname + backend port
    // Frontend is on port 5173, backend is on port 8080
    const backendPort = 8080;
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;

    return `${protocol}//${hostname}:${backendPort}${path}`;
};


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
