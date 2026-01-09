import numpy as np

def blend_images_cy(mask_warped, frame_warped, frame_rgb, result):
    """
    Pure NumPy fallback for the Cythonized blend_images_cy function.
    
    Args:
        mask_warped: np.ndarray [H, W] (float32)
        frame_warped: np.ndarray [H, W, 3] (float32)
        frame_rgb: np.ndarray [H, W, 3] (uint8)
        result: np.ndarray [H, W, 3] (uint8) output
    """
    # Expand mask to 3 channels for broadcasting: (H, W, 1)
    mask = mask_warped[:, :, np.newaxis]
    
    # Linear interpolation: mask * warped + (1 - mask) * original
    # We convert both to float for the calculation
    blended = mask * frame_warped + (1.0 - mask) * frame_rgb.astype(np.float32)
    
    # Clip and convert back to uint8
    result[:] = np.clip(blended, 0, 255).astype(np.uint8)

# Attempt to import the Cython version if it exists
try:
    # This would be the name if compiled as an extension
    # However, since we are in __init__.py and 'blend.pyx' is in the same dir,
    # usually it's compiled to 'blend.so' (on mac) or 'blend.pyd' (on windows)
    # and would be 'from .blend import blend_images_cy'
    from .blend import blend_images_cy as compiled_blend
    blend_images_cy = compiled_blend
    print("[Ditto] Using compiled Cython blend function.")
except ImportError:
    # Fallback to the NumPy version defined above
    print("[Ditto] Using NumPy fallback for blend function.")
