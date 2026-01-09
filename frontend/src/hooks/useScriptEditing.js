import { useState, useEffect } from 'react';

export function useScriptEditing(initialScriptData) {
    const [localScriptData, setLocalScriptData] = useState(initialScriptData);
    const [editingIndex, setEditingIndex] = useState(null); // Index of slide being edited, or 'opening' for opening
    const [editText, setEditText] = useState("");

    // Update local data if prop changes (e.g. regenerated or language switch)
    useEffect(() => {
        setLocalScriptData(initialScriptData);
    }, [initialScriptData]);

    const startEditing = (index, currentText) => {
        setEditingIndex(index);
        setEditText(currentText);
    };

    const cancelEditing = () => {
        setEditingIndex(null);
        setEditText("");
    };

    const saveEditing = (index) => {
        // Handle opening text editing
        if (index === 'opening') {
            const newFullScript = assembleFullScript(editText, localScriptData.slide_scripts);
            setLocalScriptData(prev => ({
                ...prev,
                opening: editText,
                full_script: newFullScript
            }));
            setEditingIndex(null);
            setEditText("");
            return;
        }

        // Handle slide script editing
        const updatedSlides = [...localScriptData.slide_scripts];
        updatedSlides[index] = {
            ...updatedSlides[index],
            script: editText
        };

        // Reconstruct full script
        // Note: This is a simple reconstruction. If structure is complex, might need more logic.
        // For now, replacing the slide content in full_script might be tricky without markers.
        // A simpler approach for the UI: Update the specific slide.
        // The 'full_script' string might be stale, but the UI primarily renders from slide_scripts for slides.
        // If we want to update full_script string too, we'd need to re-assemble it.

        const newFullScript = assembleFullScript(localScriptData.opening, updatedSlides);

        setLocalScriptData(prev => ({
            ...prev,
            slide_scripts: updatedSlides,
            full_script: newFullScript
        }));
        setEditingIndex(null);
        setEditText("");
    };

    return {
        localScriptData,
        editingIndex,
        editText,
        setEditText,
        startEditing,
        cancelEditing,
        saveEditing
    };
}

// Helper to re-assemble full script for download/copy purposes
function assembleFullScript(opening, slides) {
    let script = "";
    if (opening) {
        script += `=== 開場白 ===\n${opening}\n\n`;
    }
    slides.forEach(slide => {
        script += `--- 第 ${slide.slide_no} 頁 ---\n${slide.script}\n\n`;
    });
    return script;
}

