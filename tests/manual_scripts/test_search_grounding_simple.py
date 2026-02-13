"""
Vereinfachter Test für Google Search Grounding.
Testet die grundlegende Funktionalität mit detailliertem Output.
"""
import asyncio
import os
import sys
import json

# Füge shared zu Python Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from shared.apis.search_grounding import GoogleSearchGrounding


async def simple_test():
    """Einfacher Test der grundlegenden Funktionalität."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY nicht gesetzt")
        return
    
    print("="*70)
    print("VEREINFACHTER GOOGLE SEARCH GROUNDING TEST")
    print("="*70)
    print(f"\n✅ API Key gefunden: {api_key[:10]}...")
    
    client = GoogleSearchGrounding(api_key=api_key)
    
    # Test 1: Einfache Marktdaten-Suche mit bekanntem Buch
    print("\n" + "="*70)
    print("TEST 1: Einfache Marktdaten-Suche")
    print("="*70)
    print("\n📖 Suche nach: 1984 von George Orwell (ISBN: 9780451524935)")
    
    try:
        result = await client.search_book_market_data(
            title="1984",
            author="George Orwell",
            isbn="9780451524935"
        )
        
        print(f"\n✅ Status: {'Erfolgreich' if result.get('found_data') else 'Fehlgeschlagen'}")
        print(f"📊 Konfidenz: {result.get('confidence', 0):.2f}")
        
        if result.get('error'):
            print(f"\n⚠️ Fehler: {result['error']}")
            if result.get('raw_response'):
                print(f"\n📄 Rohe Response (erste 500 Zeichen):")
                print(result['raw_response'][:500])
        else:
            print(f"\n📚 Editionen gefunden: {len(result.get('editions', []))}")
            if result.get('availability'):
                print("💰 Verfügbarkeit: Ja")
        
        print(f"\n📋 Vollständiges Ergebnis:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Identifikation ohne ISBN (Problem-Test)
    print("\n" + "="*70)
    print("TEST 2: Identifikation ohne ISBN (bekanntes Problem)")
    print("="*70)
    print("\n📖 Suche nach: Buddenbrooks von Thomas Mann")
    
    try:
        result = await client.identify_book_without_isbn(
            title="Buddenbrooks",
            author="Thomas Mann",
            publisher="S. Fischer",
            year="1901"
        )
        
        print(f"\n✅ Status: {'Erfolgreich' if result.get('identified') else 'Fehlgeschlagen'}")
        print(f"📊 Konfidenz: {result.get('identification_confidence', 0):.2f}")
        
        if result.get('error'):
            print(f"\n⚠️ Fehler: {result['error']}")
            if result.get('raw_response'):
                print(f"\n📄 Rohe Response (erste 1000 Zeichen):")
                print(result['raw_response'][:1000])
        else:
            print(f"\n✅ ISBN gefunden: {result.get('isbn', 'Keine')}")
        
        print(f"\n📋 Vollständiges Ergebnis:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Noch einfacherer Test mit modernem Buch
    print("\n" + "="*70)
    print("TEST 3: Modernes Buch mit ISBN")
    print("="*70)
    print("\n📖 Suche nach: Harry Potter und der Stein der Weisen")
    
    try:
        result = await client.search_book_market_data(
            title="Harry Potter und der Stein der Weisen",
            author="J.K. Rowling",
            isbn="9783551551672"
        )
        
        print(f"\n✅ Status: {'Erfolgreich' if result.get('found_data') else 'Fehlgeschlagen'}")
        print(f"📊 Konfidenz: {result.get('confidence', 0):.2f}")
        
        if result.get('error'):
            print(f"\n⚠️ Fehler: {result['error']}")
        else:
            print(f"📚 Editionen: {len(result.get('editions', []))}")
        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ Test abgeschlossen")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(simple_test())