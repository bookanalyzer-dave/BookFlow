"""
Test Script für Google Search Grounding Integration
Tests die neue Search Grounding Funktionalität mit verschiedenen Szenarien.
"""
import asyncio
import os
import sys
import json
from typing import Dict, Any

# Füge shared zu Python Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from shared.apis.search_grounding import GoogleSearchGrounding
from shared.apis.data_fusion import DataFusionEngine


async def test_search_market_data():
    """Test 1: Suche nach Marktdaten für bekanntes Buch mit ISBN."""
    print("\n" + "="*70)
    print("TEST 1: Marktdaten-Suche für Buch mit ISBN")
    print("="*70)
    
    client = GoogleSearchGrounding()
    
    # Test mit einem bekannten deutschen Buch
    result = await client.search_book_market_data(
        isbn="978-3-423-14647-9",
        title="Der Vorleser",
        author="Bernhard Schlink",
        publisher="dtv",
        year="2019"
    )
    
    print(f"\n✅ Gefundene Daten: {result.get('found_data', False)}")
    print(f"📊 Konfidenz: {result.get('confidence', 0):.2f}")
    print(f"📚 Editionen gefunden: {len(result.get('editions', []))}")
    
    if result.get('editions'):
        print("\nEditionen:")
        for edition in result['editions']:
            print(f"  - {edition.get('type', 'N/A')} ({edition.get('publisher', 'N/A')}, {edition.get('year', 'N/A')})")
    
    if result.get('availability'):
        print("\nVerfügbarkeit:")
        avail = result['availability']
        if avail.get('new', {}).get('available'):
            price = avail['new'].get('price_range', {})
            print(f"  - Neu: €{price.get('min', 0):.2f} - €{price.get('max', 0):.2f}")
        if avail.get('used', {}).get('available'):
            price = avail['used'].get('price_range', {})
            print(f"  - Gebraucht: €{price.get('min', 0):.2f} - €{price.get('max', 0):.2f}")
    
    print(f"\n🔍 Search Queries verwendet: {result.get('search_queries', [])}")
    print(f"🌐 Quellen verwendet: {result.get('sources_used', [])}")
    
    return result


async def test_identify_without_isbn():
    """Test 2: Identifiziere altes Buch ohne ISBN."""
    print("\n" + "="*70)
    print("TEST 2: Identifikation ohne ISBN (Antiquarisches Buch)")
    print("="*70)
    
    client = GoogleSearchGrounding()
    
    # Test mit einem älteren deutschen Klassiker
    result = await client.identify_book_without_isbn(
        title="Buddenbrooks",
        author="Thomas Mann",
        publisher="S. Fischer",
        year="1901",
        additional_info="Verfall einer Familie, Erstausgabe"
    )
    
    print(f"\n✅ Identifikation erfolgreich: {result.get('identified', False)}")
    print(f"📊 Konfidenz: {result.get('confidence', 0):.2f}")
    
    if result.get('identified'):
        print(f"\n📖 Identifizierte Daten:")
        print(f"  Titel: {result.get('title_verified', 'N/A')}")
        print(f"  Autor: {result.get('author_verified', 'N/A')}")
        print(f"  ISBN gefunden: {result.get('isbn_found', 'Keine')}")
        print(f"  Verlag: {result.get('publisher_verified', 'N/A')}")
        print(f"  Jahr: {result.get('year_verified', 'N/A')}")
        
        if result.get('special_notes'):
            print(f"\n📝 Besondere Hinweise: {result['special_notes']}")
    
    print(f"\n🔍 Search Queries: {result.get('search_queries', [])}")
    
    return result


async def test_verify_edition():
    """Test 3: Verifiziere Edition-Details."""
    print("\n" + "="*70)
    print("TEST 3: Edition-Verifikation")
    print("="*70)
    
    client = GoogleSearchGrounding()
    
    existing_data = {
        "title": "1984",
        "author": "George Orwell",
        "publisher": "Fischer",
        "publishedDate": "2021",
        "detectedEdition": "Taschenbuch-Ausgabe"
    }
    
    result = await client.verify_edition_details(
        existing_data=existing_data
    )
    
    print(f"\n✅ Verifikation: {result.get('verified', False)}")
    print(f"📊 Konfidenz: {result.get('confidence', 0):.2f}")
    
    if result.get('edition_details'):
        details = result['edition_details']
        print(f"\n📚 Edition-Details:")
        print(f"  Typ: {details.get('type', 'N/A')}")
        print(f"  Verlag: {details.get('publisher', 'N/A')}")
        print(f"  Jahr: {details.get('year', 'N/A')}")
        print(f"  Erstausgabe: {details.get('is_first_edition', 'N/A')}")
        
        if details.get('special_features'):
            print(f"  Besonderheiten: {', '.join(details['special_features'])}")
    
    if result.get('alternative_editions'):
        print(f"\n🔄 Alternative Editionen gefunden: {len(result['alternative_editions'])}")
    
    return result


async def test_data_fusion_with_grounding():
    """Test 4: Komplette Data Fusion mit Search Grounding."""
    print("\n" + "="*70)
    print("TEST 4: Data Fusion Engine mit Search Grounding")
    print("="*70)
    
    engine = DataFusionEngine()
    
    # Test-Szenario: Buch ohne ISBN (schwierige Identifikation)
    test_data = {
        "title": "Die Verwandlung",
        "author": "Franz Kafka",
        "publisher": "Kurt Wolff Verlag",
        "publishedDate": "1915"
        # Keine ISBN!
    }
    
    print(f"\n📥 Input-Daten:")
    print(f"  Titel: {test_data['title']}")
    print(f"  Autor: {test_data['author']}")
    print(f"  ISBN: Keine")
    
    result = await engine.fuse_book_data(
        base_data=test_data,
        enable_parallel=True,
        enable_search_grounding=True
    )
    
    print(f"\n📤 Fusionierte Daten:")
    print(f"  Titel: {result.title}")
    print(f"  Autoren: {', '.join(result.authors) if result.authors else 'N/A'}")
    print(f"  ISBN: {result.isbn or 'Nicht gefunden'}")
    print(f"  Verlag: {result.publisher or 'N/A'}")
    print(f"  Erscheinungsdatum: {result.published_date or 'N/A'}")
    
    print(f"\n📊 Qualitäts-Metriken:")
    print(f"  Overall Confidence: {result.overall_confidence:.2f}")
    print(f"  Quality Score: {result.quality_score:.2f}")
    print(f"  Quellen verwendet: {', '.join(result.sources_used)}")
    print(f"  Such-Methoden: {', '.join(result.search_methods)}")
    print(f"  Fusion-Strategie: {result.fusion_strategy}")
    
    if result.description:
        print(f"\n📝 Beschreibung (Auszug):")
        print(f"  {result.description[:200]}...")
    
    return result


async def test_data_fusion_without_grounding():
    """Test 5: Data Fusion OHNE Search Grounding (Vergleich)."""
    print("\n" + "="*70)
    print("TEST 5: Data Fusion OHNE Search Grounding (Baseline)")
    print("="*70)
    
    engine = DataFusionEngine()
    
    # Gleicher Test wie Test 4, aber ohne Grounding
    test_data = {
        "title": "Die Verwandlung",
        "author": "Franz Kafka",
        "publisher": "Kurt Wolff Verlag",
        "publishedDate": "1915"
    }
    
    result = await engine.fuse_book_data(
        base_data=test_data,
        enable_parallel=True,
        enable_search_grounding=False  # Deaktiviert!
    )
    
    print(f"\n📤 Fusionierte Daten (ohne Grounding):")
    print(f"  Titel: {result.title}")
    print(f"  ISBN: {result.isbn or 'Nicht gefunden'}")
    print(f"  Confidence: {result.overall_confidence:.2f}")
    print(f"  Quality Score: {result.quality_score:.2f}")
    print(f"  Quellen: {', '.join(result.sources_used)}")
    
    return result


async def run_all_tests():
    """Führt alle Tests aus."""
    print("\n" + "="*70)
    print("🚀 GOOGLE SEARCH GROUNDING INTEGRATION TESTS")
    print("="*70)
    print("\nTeste die neue Search Grounding Funktionalität...")
    
    # Prüfe API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ FEHLER: GEMINI_API_KEY nicht gesetzt!")
        print("Bitte setze die Umgebungsvariable: export GEMINI_API_KEY='your-key'")
        return
    
    print(f"✅ API Key gefunden: {api_key[:10]}...")
    
    try:
        # Test 1: Marktdaten
        result1 = await test_search_market_data()
        
        # Test 2: Identifikation ohne ISBN
        result2 = await test_identify_without_isbn()
        
        # Test 3: Edition-Verifikation
        result3 = await test_verify_edition()
        
        # Test 4: Data Fusion MIT Grounding
        result4 = await test_data_fusion_with_grounding()
        
        # Test 5: Data Fusion OHNE Grounding (Vergleich)
        result5 = await test_data_fusion_without_grounding()
        
        # Zusammenfassung
        print("\n" + "="*70)
        print("📊 TEST-ZUSAMMENFASSUNG")
        print("="*70)
        print(f"✅ Test 1 (Marktdaten): {'Erfolgreich' if result1.get('found_data') else 'Fehlgeschlagen'}")
        print(f"✅ Test 2 (Ohne ISBN): {'Erfolgreich' if result2.get('identified') else 'Fehlgeschlagen'}")
        print(f"✅ Test 3 (Edition): {'Erfolgreich' if result3.get('verified') else 'Fehlgeschlagen'}")
        print(f"✅ Test 4 (Fusion+Grounding): Confidence={result4.overall_confidence:.2f}")
        print(f"✅ Test 5 (Fusion-Baseline): Confidence={result5.overall_confidence:.2f}")
        
        # Vergleich
        improvement = result4.overall_confidence - result5.overall_confidence
        print(f"\n📈 Improvement durch Search Grounding: {improvement:+.2f} ({improvement*100:+.1f}%)")
        
        print("\n✅ Alle Tests abgeschlossen!")
        
    except Exception as e:
        print(f"\n❌ Fehler während der Tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Führe Tests aus
    asyncio.run(run_all_tests())