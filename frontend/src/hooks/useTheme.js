import { useState, useEffect } from 'react';

/**
 * Custom hook for managing application theme
 * @returns {{theme: string, setTheme: function}}
 */
export function useTheme() {
    const [theme, setThemeState] = useState(() => {
        // Try to get from local storage
        const saved = localStorage.getItem('app-theme');
        if (saved) return saved;
        return 'dark'; // Default to dark as per user preference
    });

    useEffect(() => {
        const root = document.documentElement;

        // Remove old theme classes/attributes if any
        root.removeAttribute('data-theme');

        // Save preference
        localStorage.setItem('app-theme', theme);

        if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark'
                : 'light';
            root.setAttribute('data-theme', systemTheme);
        } else {
            root.setAttribute('data-theme', theme);
        }

    }, [theme]);

    // Listen for system theme changes if using system mode
    useEffect(() => {
        if (theme !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = (e) => {
            const newSystemTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newSystemTheme);
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [theme]);

    return { theme, setTheme: setThemeState };
}
