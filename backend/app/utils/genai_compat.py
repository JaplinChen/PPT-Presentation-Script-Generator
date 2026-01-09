"""
Google Generative AI compatibility layer.
Handles import differences between google-genai and google-generativeai packages.
"""
import logging

logger = logging.getLogger(__name__)

# Try to import the genai library
genai = None
genai_client_mode = False

try:
    import google.generativeai as genai
    genai_client_mode = False
    logger.info("Loaded google.generativeai (standard SDK)")
except ImportError:
    logger.warning("google.generativeai not found, trying google-genai")
    try:
        from google import genai
        genai_client_mode = True
        logger.info("Loaded google.genai (modern SDK)")
    except ImportError:
        logger.error("No Google GenAI library found. Please install google-generativeai.")
        genai = None


def is_genai_available() -> bool:
    """Check if genai library is available."""
    return genai is not None


def is_client_mode() -> bool:
    """Check if using Client-based API (google-genai)."""
    return genai_client_mode


def get_genai():
    """Get the genai module."""
    if genai is None:
        raise ImportError("Google GenAI library not available. Please install google-generativeai.")
    return genai
