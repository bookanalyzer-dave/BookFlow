import asyncio
import os
import logging
from unittest.mock import MagicMock, AsyncMock
from shared.apis.price_grounding import PriceGroundingClient

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_grounding_logic():
    """
    Testet die Logik des PriceGroundingClient.
    Da wir keine echten API-Keys im Test haben, mocken wir den Client.
    """
    logger.info("Starting PriceGroundingClient setup test...")
    
    # Mock den genai.Client
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content = AsyncMock()
    
    # Beispiel Response
    mock_response = MagicMock()
    mock_response.text = '{"offers": [{"seller": "Medimops", "price_eur": 12.50, "condition": "Gut", "platform": "eurobuch", "url": "http://test.com"}]}'
    mock_genai_client.models.generate_content.return_value = mock_response
    
    # Initialisiere Client mit Mock
    client = PriceGroundingClient(project_id="test-project")
    client.client = mock_genai_client
    
    # Test Search
    isbn = "9783423282388"
    logger.info(f"Testing search for ISBN {isbn}...")
    
    prices = await client.search_market_prices(isbn, "Der Gesang der Flusskrebse")
    
    assert len(prices) == 1
    assert prices[0].seller == "Medimops"
    assert prices[0].price_eur == 12.50
    
    logger.info("✅ PriceGroundingClient logic test successful!")

if __name__ == "__main__":
    asyncio.run(test_grounding_logic())
