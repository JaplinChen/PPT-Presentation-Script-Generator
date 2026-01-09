import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import zhTW from './locales/zh-TW.json';
import en from './locales/en.json';
import vi from './locales/vi.json';
import ja from './locales/ja.json';

i18n
    .use(initReactI18next)
    .init({
        resources: {
            'zh-TW': { translation: zhTW },
            'en': { translation: en },
            'vi': { translation: vi },
            'ja': { translation: ja }
        },
        lng: 'zh-TW', // 預設語言
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false // React 預設會防止 XSS
        }
    });

export default i18n;
