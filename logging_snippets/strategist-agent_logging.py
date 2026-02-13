import logging
from google.cloud import logging as cloud_logging

# Setup Cloud Logging for strategist-agent
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger('strategist-agent')
logger.setLevel(logging.INFO)

# Example structured logging
logger.info(
    "Agent processing started",
    extra={
        "agent_name": "strategist-agent",
        "user_id": user_id,
        "book_id": book_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)

# Error logging with context
try:
    # Agent logic
    pass
except Exception as e:
    logger.error(
        f"strategist-agent processing failed",
        extra={
            "agent_name": "strategist-agent",
            "error": str(e),
            "user_id": user_id,
            "book_id": book_id
        },
        exc_info=True
    )