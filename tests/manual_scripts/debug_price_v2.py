import sys
import os
import asyncio
import logging

# Add shared to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.apis.price_grounding import PriceGroundingClient, PriceGroundingConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Ensure GCP_PROJECT is set
    if not os.getenv("GCP_PROJECT"):
        os.environ["GCP_PROJECT"] = "project-52b2fab8-15a1-4b66-9f3"
        logger.info(f"Set GCP_PROJECT to {os.environ['GCP_PROJECT']}")

    isbn = "9783518459201"
    logger.info(f"Testing Price Grounding for ISBN: {isbn}")
    
    try:
        # Use explicit config if needed, but default should be fine
        config = PriceGroundingConfig(model="gemini-2.5-pro", temperature=0.1)
        client = PriceGroundingClient(config=config, location="us-central1")
        
        logger.info(f"Client initialized with model: {client.config.model}")

        # We call it with minimal args
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

