import { useState, useEffect, useCallback } from 'react';

const SESSION_KEY = 'ppt_app_session';

export function useSession() {
    const [hasSavedSession, setHasSavedSession] = useState(false);
    const [savedSessionData, setSavedSessionData] = useState(null);

    // Initial check
    useEffect(() => {
        try {
            const saved = localStorage.getItem(SESSION_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                // Basic validation
                if (parsed.fileId) {
                    setHasSavedSession(true);
                    setSavedSessionData(parsed);
                }
            }
        } catch (e) {
            console.error("Failed to parse saved session", e);
        }
    }, []);

    const saveSession = useCallback((data) => {
        try {
            const session = {
                timestamp: Date.now(),
                ...data
            };
            localStorage.setItem(SESSION_KEY, JSON.stringify(session));
        } catch (e) {
            console.error("Failed to save session", e);
        }
    }, []);

    const clearSession = useCallback(() => {
        localStorage.removeItem(SESSION_KEY);
        setHasSavedSession(false);
        setSavedSessionData(null);
    }, []);

    return {
        hasSavedSession,
        savedSessionData,
        saveSession,
        clearSession
    };
}
