"""
Debug-Test für Google Search Grounding Metadata.
Prüft ob Google Search tatsächlich aktiv genutzt wird.
"""
import asyncio
import os
import sys
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Füge shared zu Python Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from google import genai
from google.genai import types


async def test_grounding_metadata():
    """Test Google Search Grounding mit detaillierter Metadata-Analyse."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt")
        return
    
    print("="*80)
    print("GOOGLE SEARCH GROUNDING METADATA DEBUG TEST")
    print("="*80)
    print(f"\nAPI Key: {api_key[:10]}...")
    
    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-pro"
    
    # Test 1: Einfache Buchsuche
    print("\n" + "="*80)
    print("TEST 1: Einfache Buchsuche mit Google Search")
    print("="*80)
    
    prompt = """
Suche auf Google nach aktuellem Preis und Verfügbarkeit für:
Titel: "1984"
Autor: "George Orwell"
ISBN: "9780451524935"

Gib mir die aktuellen Preise in JSON zurück:
{
  "found": true/false,
  "price_new": 0.0,
  "price_used": 0.0,
  "available": true/false
}
"""
    
    try:
        print("\nSende Anfrage an Gemini 2.5 Pro mit Google Search Tool...")
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.1
            )
        )
        
        print("\n" + "-"*80)
        print("RESPONSE ANALYSE")
        print("-"*80)
        
        # Response Text
        print(f"\nResponse Text (erste 500 Zeichen):")
        print(response.text[:500] if response.text else "LEER")
        
        # Kandidaten
        if response.candidates:
            print(f"\nAnzahl Kandidaten: {len(response.candidates)}")
            candidate = response.candidates[0]
            
            # Grounding Metadata prüfen
            print("\n" + "-"*80)
            print("GROUNDING METADATA ANALYSE")
            print("-"*80)
            
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata
                print("\n✅ Grounding Metadata VORHANDEN!")
                
                # Web Search Queries
                if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                    print(f"\n📍 Web Search Queries ({len(metadata.web_search_queries)}):")
                    for i, query in enumerate(metadata.web_search_queries, 1):
                        print(f"  {i}. {query}")
                else:
                    print("\n⚠️ KEINE web_search_queries gefunden!")
                    print("   Das deutet darauf hin, dass Google Search NICHT verwendet wurde!")
                
                # Search Entry Point
                if hasattr(metadata, 'search_entry_point'):
                    print(f"\n🔍 Search Entry Point: {metadata.search_entry_point}")
                
                # Grounding Chunks (Quellen)
                if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                    print(f"\n📚 Grounding Chunks ({len(metadata.grounding_chunks)}):")
                    for i, chunk in enumerate(metadata.grounding_chunks, 1):
                        if hasattr(chunk, 'web'):
                            print(f"\n  Chunk {i}:")
                            print(f"    Title: {chunk.web.title if hasattr(chunk.web, 'title') else 'N/A'}")
                            print(f"    URI: {chunk.web.uri if hasattr(chunk.web, 'uri') else 'N/A'}")
                else:
                    print("\n⚠️ KEINE grounding_chunks gefunden!")
                    print("   Keine Quellen aus Google Search verwendet!")
                
                # Grounding Support
                if hasattr(metadata, 'grounding_supports'):
                    print(f"\n✓ Grounding Supports: {len(metadata.grounding_supports)} Items")
                
            else:
                print("\n❌ KEINE Grounding Metadata gefunden!")
                print("   Google Search wurde NICHT verwendet!")
                print("   Möglicherweise wurde nur das Modell-Wissen genutzt!")
            
            # Finish Reason
            if hasattr(candidate, 'finish_reason'):
                print(f"\n🏁 Finish Reason: {candidate.finish_reason}")
            
            # Safety Ratings
            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                print(f"\n🛡️ Safety Ratings: {len(candidate.safety_ratings)} Kategorien")
        
        else:
            print("\n❌ Keine Kandidaten in Response!")
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Explizite Search-Anforderung
    print("\n\n" + "="*80)
    print("TEST 2: Explizite Google Search Anforderung")
    print("="*80)
    
    prompt2 = """
Nutze GOOGLE SEARCH um aktuelle Informationen zu finden!

Suche nach: "1984 George Orwell current price"

Was findest du über den aktuellen Preis?
"""
    
    try:
        print("\nSende explizite Search-Anfrage...")
        
        response2 = client.models.generate_content(
            model=model,
            contents=prompt2,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.1
            )
        )
        
        print(f"\nResponse: {response2.text[:300]}...")
        
        if response2.candidates and response2.candidates[0].grounding_metadata:
            metadata2 = response2.candidates[0].grounding_metadata
            
            if hasattr(metadata2, 'web_search_queries') and metadata2.web_search_queries:
                print(f"\n✅ Google Search AKTIV verwendet!")
                print(f"   Queries: {metadata2.web_search_queries}")
            else:
                print("\n⚠️ Google Search NICHT verwendet trotz expliziter Anforderung!")
        else:
            print("\n❌ Keine Grounding Metadata!")
    
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
    
    print("\n" + "="*80)
    print("DEBUG TEST ABGESCHLOSSEN")
    print("="*80)
    print("\n💡 Interpretation:")
    print("  - Wenn 'web_search_queries' leer ist: Google Search wird NICHT genutzt")
    print("  - Wenn 'grounding_chunks' leer ist: Keine externen Quellen verwendet")
    print("  - Nur Modell-Wissen wird genutzt, NICHT aktuelles Google Search")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_grounding_metadata())