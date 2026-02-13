import logging
from google.cloud import logging as cloud_logging

# Setup Cloud Logging for ambassador-agent
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger('ambassador-agent')
logger.setLevel(logging.INFO)

# Example structured logging
logger.info(
    "Agent processing started",
    extra={
        "agent_name": "ambassador-agent",
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
        f"ambassador-agent processing failed",
        extra={
            "agent_name": "ambassador-agent",
            "error": str(e),
            "user_id": user_id,
            "book_id": book_id
        },
        exc_info=True
    )