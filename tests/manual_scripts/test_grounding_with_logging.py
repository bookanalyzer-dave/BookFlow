"""
Test mit verbessertem Grounding-Debug-Logging.
"""
import asyncio
import os
import sys
import logging

# Setup logging to see DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Füge shared zu Python Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from shared.apis.search_grounding import GoogleSearchGrounding


async def test_with_logging():
    """Test mit vollständigem Debug-Logging."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Try to load from env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        except:
            pass
    
    if not api_key:
        print("\n❌ GEMINI_API_KEY nicht verfügbar")
        print("Bitte setzen: export GEMINI_API_KEY='your-key'")
        return
    
    print("="*80)
    print("GOOGLE SEARCH GROUNDING TEST MIT DEBUG-LOGGING")
    print("="*80)
    print(f"\n✅ API Key vorhanden: {api_key[:10]}...")
    
    client = GoogleSearchGrounding(api_key=api_key)
    
    print("\n" + "-"*80)
    print("TEST: Marktdaten-Suche für '1984' von George Orwell")
    print("-"*80 + "\n")
    
    result = await client.search_book_market_data(
        title="1984",
        author="George Orwell",
        isbn="9780451524935"
    )
    
    print("\n" + "="*80)
    print("ERGEBNIS")
    print("="*80)
    print(f"Found Data: {result.get('found_data')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"\n🔍 GROUNDING STATUS:")
    print(f"  - Grounding Active: {result.get('_grounding_active', False)}")
    print(f"  - Web Search Queries: {result.get('_web_search_queries', [])}")
    print(f"  - Source URLs: {len(result.get('_source_urls', []))} URLs")
    
    if result.get('_source_urls'):
        print(f"\n📚 Sources:")
        for i, url in enumerate(result['_source_urls'][:5], 1):
            print(f"  {i}. {url}")
    
    if result.get('editions'):
        print(f"\n📖 Editions: {len(result['editions'])}")
        for ed in result['editions'][:3]:
            print(f"  - {ed.get('type')} ({ed.get('publisher')}, {ed.get('year')})")
    
    if result.get('error'):
        print(f"\n⚠️ Error: {result['error']}")
    
    print("\n" + "="*80)
    
    # Interpretation
    if result.get('_grounding_active'):
        print("✅ ERFOLG: Google Search Grounding wurde aktiv genutzt!")
    else:
        print("❌ PROBLEM: Google Search wurde NICHT aktiviert!")
        print("   → Das bedeutet: Nur Modell-Wissen, keine Live-Daten!")


if __name__ == "__main__":
    asyncio.run(test_with_logging())