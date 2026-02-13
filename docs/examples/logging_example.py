# Example: Add to agent main.py
import logging.config
import json

# Load logging config
with open('logging_config.json', 'r') as f:
    config = json.load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Processing started", extra={
    "user_id": user_id,
    "book_id": book_id,
    "agent": "ingestion-agent"
})