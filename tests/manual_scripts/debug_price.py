import sys
import os
import asyncio
import logging

# Add shared to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.apis.price_grounding import PriceGroundingClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Set GCP Project if not set. Try to infer or set a default if running locally without env var.
    if not os.getenv("GCP_PROJECT"):
        # Try to read from .env if exists, or just warn
        logger.warning("GCP_PROJECT not set. Assuming 'book-quest-app' or reliant on default credentials.")
        # os.environ["GCP_PROJECT"] = "book-quest-app" 

    isbn = "9783861500268"
    logger.info(f"Testing Price Grounding for ISBN: {isbn}")
    
    try:
        client = PriceGroundingClient()
        # We call it with minimal args like in the reported issue (presumably)
        result = await client.search_market_prices(isbn=isbn)
        
        print("\n--- Result Summary ---")
        print(f"Confidence: {result.confidence_score}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Offers found: {len(result.offers)}")
        for offer in result.offers:
            print(f"- {offer.price_eur} EUR ({offer.condition}) via {offer.platform} [{offer.seller}]")
            
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
