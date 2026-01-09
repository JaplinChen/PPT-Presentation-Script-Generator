import logging
import sys
from app.core.config import settings

class EndpointFilter(logging.Filter):
    """
    Filter out health checks and status polling logs to keep console clean.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return (
            msg.find("/status HTTP/1.1\" 200") == -1 and 
            msg.find("/health HTTP/1.1\" 200") == -1 and 
            msg.find("/api/avatar/system-info HTTP/1.1\" 200") == -1 and
            msg.find("/api/job/") == -1 # Reduce job polling noise if needed
        )

def setup_logging():
    """
    Configure logging for the application.
    """
    # Base configuration
    logging.basicConfig(
        level=logging.INFO if settings.DEBUG else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google.generativeai").setLevel(logging.WARNING)
    
    # Ensure app logger is set
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    
    return logger

logger = setup_logging()
