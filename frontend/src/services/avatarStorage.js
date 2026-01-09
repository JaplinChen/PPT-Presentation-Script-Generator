/**
 * Avatar Settings Storage Service
 * Manages saved avatar photos and preferences in localStorage.
 */

const STORAGE_KEY = 'avatar_settings';

/**
 * Generate UUID compatible with both secure and non-secure contexts.
 * crypto.randomUUID() only works in HTTPS or localhost.
 */
const generateUUID = () => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    // Fallback for HTTP contexts (LAN access)
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const defaultSettings = {
    photos: [],
    defaultPhotoId: null,
    preferences: {
        emotion: 4,
        crop_scale: 2.5, // Default to Wide/Standard
        sampling_steps: 20, // Default to Fast/Standard
        max_size: 480 // Default to SD for PPT optimization
    }
};

export const avatarStorage = {
    /**
     * Load settings from localStorage
     */
    load() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) return defaultSettings;
        try {
            const parsed = JSON.parse(saved);
            // 數據遷移/修復：確保所有照片都有 photo_url 欄位 (相容舊版 url_path)
            if (parsed.photos) {
                parsed.photos = parsed.photos.map(p => ({
                    ...p,
                    photo_url: p.photo_url || p.url_path || ''
                }));
            }
            return { ...defaultSettings, ...parsed };
        } catch (e) {
            console.error('Failed to parse avatar settings', e);
            return defaultSettings;
        }
    },

    /**
     * Save settings to localStorage
     */
    save(settings) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    },

    /**
     * Add a photo to storage
     */
    addPhoto(photo) {
        const settings = this.load();
        const newPhoto = {
            ...photo,
            photo_url: photo.photo_url || photo.url_path || '',
            id: photo.id || generateUUID(),
            uploadedAt: Date.now(),
            isDefault: settings.photos.length === 0 // First photo is default
        };

        settings.photos.push(newPhoto);
        if (newPhoto.isDefault) {
            settings.defaultPhotoId = newPhoto.id;
        }

        this.save(settings);
        return newPhoto;
    },

    /**
     * Remove a photo from storage
     */
    removePhoto(id) {
        const settings = this.load();
        settings.photos = settings.photos.filter(p => p.id !== id);

        if (settings.defaultPhotoId === id) {
            settings.defaultPhotoId = settings.photos.length > 0 ? settings.photos[0].id : null;
            if (settings.defaultPhotoId) {
                const defaultIdx = settings.photos.findIndex(p => p.id === settings.defaultPhotoId);
                if (defaultIdx !== -1) settings.photos[defaultIdx].isDefault = true;
            }
        }

        this.save(settings);
    },

    /**
     * Set a photo as default
     */
    setDefaultPhoto(id) {
        const settings = this.load();
        settings.photos = settings.photos.map(p => ({
            ...p,
            isDefault: p.id === id
        }));
        settings.defaultPhotoId = id;
        this.save(settings);
    },

    /**
     * Get default photo
     */
    getDefaultPhoto() {
        const settings = this.load();
        return settings.photos.find(p => p.id === settings.defaultPhotoId) || null;
    },

    /**
     * Update preferences
     */
    updatePreferences(prefs) {
        const settings = this.load();
        settings.preferences = { ...settings.preferences, ...prefs };
        this.save(settings);
    }
};
