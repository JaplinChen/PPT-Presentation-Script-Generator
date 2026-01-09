"""
Ditto TalkingHead 服務模組

此模組提供數位播報員生成功能的封裝介面
"""

from .config import DittoConfig
from .stream_pipeline import StreamSDK

__all__ = ['DittoConfig', 'StreamSDK']
