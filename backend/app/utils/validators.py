import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ImageValidator:
    """Helper class for validating images for avatar generation."""

    @staticmethod
    def validate(image_path: str) -> Dict:
        """Sync validation logic using OpenCV."""
        try:
            import cv2
            import numpy as np
            # Read image using imdecode to support non-ASCII paths on Windows
            # img = cv2.imread(image_path) 
            stream = np.fromfile(image_path, dtype=np.uint8)
            img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            if img is None:
                return {
                    "valid": False,
                    "message": "無法讀取圖片檔案",
                    "face_count": 0
                }
            
            # Check resolution
            h, w = img.shape[:2]
            if h < 256 or w < 256:
                return {
                    "valid": False,
                    "message": f"圖片解析度過低 ({w}x{h}),建議至少 512x512",
                    "face_count": 0
                }
            
            
            # Face detection
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return {
                    "valid": False,
                    "message": "未檢測到人臉,請使用清晰的正面人臉照片",
                    "face_count": 0
                }
            
            if len(faces) > 1:
                return {
                    "valid": False,
                    "message": f"檢測到 {len(faces)} 張人臉,請使用只有一個人的照片",
                    "face_count": len(faces)
                }
            
            # Check face size ratio
            (x, y, w_face, h_face) = faces[0]
            face_ratio = (w_face * h_face) / (w * h)
            
            if face_ratio < 0.05:
                return {
                    "valid": False,
                    "message": "人臉在照片中佔比過小,請使用人臉較大的照片",
                    "face_count": 1
                }
            
            return {
                "valid": True,
                "message": "照片驗證通過",
                "face_count": 1,
                "face_bbox": [int(x), int(y), int(w_face), int(h_face)],
                "image_size": [w, h]
            }
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return {
                "valid": False,
                "message": f"驗證過程發生錯誤: {str(e)}",
                "face_count": 0
            }
