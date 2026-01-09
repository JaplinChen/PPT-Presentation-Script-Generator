import { useState, useEffect } from 'react';
import { api } from '../services/api';
import './GenerationStep.css';

export default function TTSConfig({ onConfigChange, initialConfig }) {
    const [voices, setVoices] = useState([]);
    const [config, setConfig] = useState(initialConfig || {
        language: 'zh',
        voice: 'zh-TW-HsiaoChenNeural',
        rate: '+0%',
        pitch: '+0Hz'
    });
    const [loading, setLoading] = useState(false);

    const languages = [
        { code: 'zh', label: '繁體中文' },
        { code: 'en', label: 'English' },
        { code: 'ja', label: '日本語' },
        { code: 'vi', label: 'Tiếng Việt' }
    ];

    useEffect(() => {
        let active = true;
        const fetchVoices = async () => {
            setLoading(true);
            try {
                const data = await api.getTTSVoices(config.language);
                if (!active) return;
                setVoices(data);
                if (data.length > 0 && !data.find(v => v.short_name === config.voice)) {
                    handleUpdate({ voice: data[0].short_name });
                }
            } catch (err) {
                if (active) console.error("Failed to load voices:", err);
            } finally {
                if (active) setLoading(false);
            }
        };
        fetchVoices();
        return () => { active = false; };
    }, [config.language]);

    const handleUpdate = (updates) => {
        const newConfig = { ...config, ...updates };
        setConfig(newConfig);
        if (onConfigChange) onConfigChange(newConfig);
    };

    const langBtnStyle = (isActive) => ({
        padding: '8px 16px',
        borderRadius: '8px',
        fontSize: '13px',
        fontWeight: 600,
        cursor: 'pointer',
        border: isActive ? '2px solid #2563eb' : '1px solid #e2e8f0',
        background: isActive ? '#2563eb' : '#fff',
        color: isActive ? '#fff' : '#475569',
        transition: 'all 0.15s ease',
        marginRight: '8px',
        marginBottom: '8px'
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Language Selection */}
            <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#334155', marginBottom: '12px' }}>
                    語言 (Language)
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                    {languages.map(lang => (
                        <button
                            key={lang.code}
                            onClick={() => handleUpdate({ language: lang.code })}
                            style={langBtnStyle(config.language === lang.code)}
                        >
                            {lang.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Voice Selection */}
            <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#334155', marginBottom: '12px' }}>
                    語音角色 (Voice)
                </label>
                <select
                    value={config.voice}
                    onChange={(e) => handleUpdate({ voice: e.target.value })}
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '12px 16px',
                        fontSize: '14px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '10px',
                        background: '#fff',
                        cursor: 'pointer',
                        outline: 'none'
                    }}
                >
                    {loading ? (
                        <option>載入中...</option>
                    ) : voices.length === 0 ? (
                        <option value="">(無可用語音)</option>
                    ) : (
                        voices.map(v => (
                            <option key={v.short_name} value={v.short_name}>
                                {v.friendly_name || v.short_name} ({v.gender === 'Female' ? '女聲' : '男聲'})
                            </option>
                        ))
                    )}
                </select>
            </div>

            {/* Speed Slider */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label style={{ fontSize: '14px', fontWeight: 600, color: '#334155' }}>語速 (Rate)</label>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '4px 10px', borderRadius: '6px' }}>{config.rate}</span>
                </div>
                <input
                    type="range"
                    min="-50" max="50" step="5"
                    value={parseInt(config.rate.replace('%', '')) || 0}
                    onChange={(e) => {
                        const val = parseInt(e.target.value);
                        handleUpdate({ rate: `${val >= 0 ? '+' : ''}${val}%` });
                    }}
                    style={{ width: '100%', accentColor: '#2563eb' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: '#94a3b8' }}>
                    <span>慢</span>
                    <span>正常</span>
                    <span>快</span>
                </div>
            </div>

            {/* Pitch Slider */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <label style={{ fontSize: '14px', fontWeight: 600, color: '#334155' }}>音調 (Pitch)</label>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '4px 10px', borderRadius: '6px' }}>{config.pitch}</span>
                </div>
                <input
                    type="range"
                    min="-20" max="20" step="1"
                    value={parseInt(config.pitch.replace('Hz', '')) || 0}
                    onChange={(e) => {
                        const val = parseInt(e.target.value);
                        handleUpdate({ pitch: `${val >= 0 ? '+' : ''}${val}Hz` });
                    }}
                    style={{ width: '100%', accentColor: '#2563eb' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: '#94a3b8' }}>
                    <span>低沉</span>
                    <span>正常</span>
                    <span>高昂</span>
                </div>
            </div>
        </div>
    );
}
