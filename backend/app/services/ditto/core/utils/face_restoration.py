
import os
import torch
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

class FaceRestorer:
    def __init__(self, device='cuda', upscale=1.0):
        self.device = device
        self.upscale = upscale # Usually 1 if we just want restoration, or 2/4 for upscaling. For Ditto, we want 1 or 2.
        self.restorer = None
        self.is_available = False
        
        try:
            from gfpgan import GFPGANer
            self.GFPGANer = GFPGANer
            self.is_available = True
            
            # Auto-download model to backend/weights/GFPGANv1.4.pth or usage default
            # GFPGANer automatically handles downloads if model_path is a url or None with version
            pass
        except ImportError:
            logger.warning("GFPGAN not installed. Face restoration will be disabled.")
            self.is_available = False

    def load_model(self):
        if not self.is_available:
            return

        if self.restorer is not None:
            return

        try:
            # Initialize GFPGANer
            # This triggers download if not found
            # Use v1.4 for best quality
            self.restorer = self.GFPGANer(
                model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth',
                upscale=self.upscale,
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=None,
                device=self.device
            )
            logger.info(f"GFPGAN model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load GFPGAN model: {e}")
            self.is_available = False

    def enhance(self, img_rgb):
        """
        Enhance the input image (RGB numpy array).
        Returns enhanced image (RGB numpy array).
        """
        if not self.is_available or self.restorer is None:
            return img_rgb

        try:
            # GFPGAN expects BGR image in 0-255 uint8 range
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            
            # restore
            # cropped_faces, restored_faces, restored_img
            # We treat the input as a whole image (which is the cropped 512x512 face from Ditto)
            _, _, restored_img_bgr = self.restorer.enhance(
                img_bgr,
                has_aligned=False, # It's roughly aligned but let's say False to be safe or True if we trust Ditto crop
                only_center_face=False,
                paste_back=True
            )
            
            if restored_img_bgr is not None:
                 return cv2.cvtColor(restored_img_bgr, cv2.COLOR_BGR2RGB)
            else:
                 return img_rgb
                 
        except Exception as e:
            logger.error(f"Error during face enhancement: {e}")
            return img_rgb
