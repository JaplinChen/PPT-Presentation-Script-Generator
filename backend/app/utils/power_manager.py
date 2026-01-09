import ctypes
import logging

logger = logging.getLogger(__name__)

# Windows API constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

class PowerManager:
    """
    Utility to prevent Windows from going to sleep during long tasks.
    """
    
    @staticmethod
    def prevent_sleep():
        """
        Prevent system sleep and display turn-off.
        """
        try:
            # Set thread execution state to prevent system sleep and display turn off
            # running in continuous mode until explicitly cleared
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            logger.info("🛡️ Power Manager: System sleep prevented.")
        except Exception as e:
            logger.warning(f"Failed to set power state: {e}")

    @staticmethod
    def allow_sleep():
        """
        Restore default power settings (allow sleep).
        """
        try:
            # Clear flags to restore standard behavior
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.info("🛡️ Power Manager: System sleep allowed.")
        except Exception as e:
            logger.warning(f"Failed to reset power state: {e}")
