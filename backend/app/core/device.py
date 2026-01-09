import logging
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

class DeviceManager:
    """Centralized manager for hardware device detection and selection."""
    
    def __init__(self):
        self._device = "cpu"
        self._checked = False

    async def get_device(self) -> str:
        """Coroutine to get the best available device."""
        if not self._checked:
            await self._check_hardware()
        return self._device

    async def _check_hardware(self):
        """Lazy check for GPU/MPS availability in a thread."""
        def _sync_check():
            try:
                import torch
                if torch.cuda.is_available():
                    self._device = "cuda"
                    logger.info("Using CUDA device")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self._device = "mps"
                    logger.info("Using Apple MPS device")
                else:
                    self._device = "cpu"
                    logger.info("Using CPU device")
                
                # Optimization: 
                # When running multiple worker threads (like in stream_pipeline), 
                # getting torch to use all cores for every op causes massive thrashing.
                # Limiting it to 1 thread per op allows the worker threads to parallelize efficiently.
                if self._device == "cpu":
                     logger.info("Setting torch.set_num_threads(1) to avoid CPU contention.")
                     torch.set_num_threads(1)
            except ImportError:
                logger.error("Torch not found")
                self._device = "cpu"
            except Exception as e:
                logger.error(f"Error checking device availability: {e}")
                self._device = "cpu"
        
        await asyncio.to_thread(_sync_check)
        self._checked = True

    async def get_system_info(self) -> Dict:
        """Get detailed system hardware info."""
        if not self._checked:
            await self._check_hardware()
            
        def _build_info():
            try:
                import torch
                info = {
                    "cuda_available": torch.cuda.is_available(),
                    "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(),
                    "device": self._device,
                }
                
                if torch.cuda.is_available():
                    try:
                        info.update({
                            "gpu_name": torch.cuda.get_device_name(0),
                            "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / 1024**3,
                            "gpu_memory_allocated": torch.cuda.memory_allocated(0) / 1024**3,
                        })
                    except Exception as e:
                        logger.error(f"Failed to get GPU details: {e}")
                elif info["mps_available"]:
                    info["gpu_name"] = "Apple Metal Performance Shaders (MPS)"
                
                return info
            except ImportError:
                return {"error": "Torch not installed"}
            except Exception as e:
                return {"error": str(e)}

        return await asyncio.to_thread(_build_info)

# Global instance
device_manager = DeviceManager()
