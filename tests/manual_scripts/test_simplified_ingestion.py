"""
Test für die Simplified Book Ingestion Pipeline.

Dieser interaktive Test demonstriert die neue vereinfachte Pipeline:
- Lädt Bilder aus test_books/
- Ruft Gemini API mit Google Search Grounding auf
- Zeigt formatierte Ergebnisse

Requirements:
    - GEMINI_API_KEY muss als Environment Variable gesetzt sein
    - google-generativeai package installiert
    - Bilder in test_books/ Ordner

Usage:
    python test_simplified_ingestion.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from shared.simplified_ingestion import (
        ingest_book_with_gemini,
        ingest_book_with_retry,
        BookIngestionRequest,
        BookIngestionResult,
        IngestionConfig,
        IngestionException,
    )
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running from the project root directory")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_BOOKS_DIR = Path("test_books")
OUTPUT_DIR = Path("test_results")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_environment():
    """Prüft ob alle Requirements erfüllt sind."""
    print("=" * 80)
    print("🔍 ENVIRONMENT CHECK")
    print("=" * 80)
    
    # Check API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY ist nicht gesetzt!")
        print("\nBitte setze den API Key:")
        print("   export GEMINI_API_KEY=your_key_here")
        print("\nAPI Key erhalten: https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✅ GEMINI_API_KEY: {api_key[:10]}...{api_key[-5:]}")
    
    # Check test_books directory
    if not TEST_BOOKS_DIR.exists():
        print(f"❌ {TEST_BOOKS_DIR} Ordner existiert nicht!")
        return False
    
    images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
    if not images:
        print(f"❌ Keine Bilder in {TEST_BOOKS_DIR} gefunden!")
        return False
    
    print(f"✅ Test Books Ordner: {len(images)} Bilder gefunden")
    
    # Check google-generativeai
    try:
        import google.generativeai as genai
        print("✅ google-generativeai package installiert")
    except ImportError:
        print("❌ google-generativeai nicht installiert!")
        print("   pip install google-generativeai")
        return False
    
    print("\n✅ Alle Checks bestanden!\n")
    return True


def print_result(result: BookIngestionResult, index: int = 0):
    """Druckt formatiertes Ergebnis."""
    print("\n" + "=" * 80)
    print(f"📚 BUCH #{index + 1} - ERGEBNIS")
    print("=" * 80)
    
    if not result.success:
        print("❌ Ingestion fehlgeschlagen!")
        print(f"   Confidence: {result.confidence:.2f}")
        return
    
    # Status
    status = result.get_firestore_status()
    status_emoji = "✅" if status == "ingested" else "⚠️"
    print(f"\n{status_emoji} Status: {status}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Processing Time: {result.processing_time_ms:.0f}ms")
    
    # Book Data
    if result.book_data:
        book = result.book_data
        print(f"\n📖 Buchdaten:")
        print(f"   Titel: {book.title}")
        
        if book.authors:
            print(f"   Autor(en): {', '.join(book.authors)}")
        
        if book.isbn_13 or book.isbn_10:
            isbn = book.isbn_13 or book.isbn_10
            print(f"   ISBN: {isbn}")
        
        if book.publisher:
            print(f"   Verlag: {book.publisher}")
        
        if book.publication_year:
            print(f"   Jahr: {book.publication_year}")
        
        if book.edition:
            print(f"   Edition: {book.edition}")
        
        if book.page_count:
            print(f"   Seiten: {book.page_count}")
        
        if book.language:
            print(f"   Sprache: {book.language}")
        
        if book.genre:
            print(f"   Genre: {', '.join(book.genre)}")
        
        if book.description:
            desc = book.description[:150] + "..." if len(book.description) > 150 else book.description
            print(f"   Beschreibung: {desc}")
        
        # Marktdaten wurden entfernt
    
    # Grounding Metadata
    print(f"\n🔍 Google Search Grounding:")
    print(f"   Aktiv: {'✅ Ja' if result.grounding_metadata.search_active else '❌ Nein'}")
    
    if result.grounding_metadata.queries_used:
        print(f"   Suchanfragen ({len(result.grounding_metadata.queries_used)}):")
        for query in result.grounding_metadata.queries_used[:3]:
            print(f"      - {query}")
    
    if result.grounding_metadata.source_urls:
        print(f"   Quellen ({len(result.grounding_metadata.source_urls)}):")
        for url in result.grounding_metadata.source_urls[:3]:
            print(f"      - {url}")
    
    if result.sources_used:
        print(f"   Verwendete APIs: {', '.join(result.sources_used)}")
    
    print("\n" + "=" * 80)


def save_result(result: BookIngestionResult, test_name: str):
    """Speichert Ergebnis als JSON."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"{test_name}_{timestamp}.json"
    
    # Convert to dict
    result_dict = {
        "success": result.success,
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms,
        "timestamp": result.timestamp.isoformat(),
        "book_data": result.book_data.model_dump() if result.book_data else None,
        "grounding_metadata": result.grounding_metadata.model_dump(),
        "sources_used": result.sources_used,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Result saved to: {output_file}")


# ============================================================================
# TESTS
# ============================================================================

async def test_single_book():
    """Test mit einem einzelnen Buch."""
    print("\n" + "=" * 80)
    print("🧪 TEST 1: Einzelnes Buch")
    print("=" * 80)
    
    # Finde erstes Bild
    images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
    if not images:
        print("❌ Keine Bilder gefunden!")
        return
    
    image_path = images[0]
    print(f"\n📸 Verwende Bild: {image_path.name}")
    
    # Create Request
    request = BookIngestionRequest(
        book_id="test_001",
        user_id="test_user",
        image_urls=[image_path.resolve().as_uri()]
    )
    
    # Run Ingestion
    print("\n⏳ Starte Ingestion mit Gemini + Google Search Grounding...")
    result = await ingest_book_with_gemini(request)
    
    # Print Result
    print_result(result)
    
    # Save Result
    save_result(result, "single_book")
    
    return result


async def test_multiple_images():
    """Test mit mehreren Bildern eines Buchs."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Multiple Bilder")
    print("=" * 80)
    
    # Finde bis zu 3 Bilder
    images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
    if not images:
        print("❌ Keine Bilder gefunden!")
        return
    
    image_paths = [img.resolve().as_uri() for img in images[:3]]
    print(f"\n📸 Verwende {len(image_paths)} Bilder:")
    for img in image_paths:
        print(f"   - {Path(img).name}")
    
    # Create Request
    request = BookIngestionRequest(
        book_id="test_002",
        user_id="test_user",
        image_urls=image_paths
    )
    
    # Run Ingestion
    print("\n⏳ Starte Ingestion...")
    result = await ingest_book_with_gemini(request)
    
    # Print Result
    print_result(result)
    
    # Save Result
    save_result(result, "multiple_images")
    
    return result


async def test_with_retry():
    """Test mit Retry Logic."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Mit Retry Logic")
    print("=" * 80)
    
    # Finde erstes Bild
    images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
    if not images:
        print("❌ Keine Bilder gefunden!")
        return
    
    image_path = images[0]
    print(f"\n📸 Verwende Bild: {image_path.name}")
    
    # Create Request
    request = BookIngestionRequest(
        book_id="test_003",
        user_id="test_user",
        image_urls=[image_path.resolve().as_uri()]
    )
    
    # Custom Config mit niedrigerem Retry
    config = IngestionConfig(
        retry_attempts=2,
        retry_delay_seconds=1.0
    )
    
    # Run Ingestion with Retry
    print("\n⏳ Starte Ingestion mit Retry Logic...")
    result = await ingest_book_with_retry(request, config=config)
    
    # Print Result
    print_result(result)
    
    # Save Result
    save_result(result, "with_retry")
    
    return result


async def test_all_books():
    """Test mit allen Büchern im Ordner."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: Alle Bücher")
    print("=" * 80)
    
    # Finde alle Bilder
    images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
    if not images:
        print("❌ Keine Bilder gefunden!")
        return
    
    print(f"\n📚 Teste {len(images)} Bücher...")
    
    results = []
    for i, image_path in enumerate(images):
        print(f"\n📸 [{i+1}/{len(images)}] Teste: {image_path.name}")
        
        # Create Request
        request = BookIngestionRequest(
            book_id=f"test_{i:03d}",
            user_id="test_user",
            image_urls=[image_path.resolve().as_uri()]
        )
        
        # Run Ingestion
        try:
            result = await ingest_book_with_gemini(request)
            results.append(result)
            print_result(result, i)
        except Exception as e:
            print(f"❌ Fehler bei {image_path.name}: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"Total: {len(results)} Bücher")
    
    successful = sum(1 for r in results if r.success)
    print(f"Erfolgreich: {successful} ({successful/len(results)*100:.1f}%)")
    
    high_conf = sum(1 for r in results if r.confidence >= 0.7)
    print(f"Hohe Confidence (≥0.7): {high_conf} ({high_conf/len(results)*100:.1f}%)")
    
    avg_conf = sum(r.confidence for r in results) / len(results)
    print(f"Durchschnittliche Confidence: {avg_conf:.2%}")
    
    avg_time = sum(r.processing_time_ms for r in results) / len(results)
    print(f"Durchschnittliche Zeit: {avg_time:.0f}ms")
    
    grounding_active = sum(1 for r in results if r.grounding_metadata.search_active)
    print(f"Google Search aktiv: {grounding_active} ({grounding_active/len(results)*100:.1f}%)")
    
    return results


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Hauptfunktion."""
    print("\n" + "=" * 80)
    print("🚀 SIMPLIFIED BOOK INGESTION PIPELINE - TEST")
    print("=" * 80)
    
    # Check Environment
    if not check_environment():
        return
    
    # Run Tests
    try:
        # Test 1: Single Book
        await test_single_book()
        
        # Test 2: Multiple Images (optional, wenn genug Bilder da sind)
        images = list(TEST_BOOKS_DIR.glob("*.jpg")) + list(TEST_BOOKS_DIR.glob("*.png"))
        if len(images) >= 2:
            await test_multiple_images()
        
        # Test 3: With Retry
        await test_with_retry()
        
        # Test 4: All Books (optional)
        # await test_all_books()
        
    except KeyboardInterrupt:
        print("\n\n❌ Test abgebrochen")
    except IngestionException as e:
        logger.error(f"Test fehlgeschlagen: {e.error.error_message}", exc_info=True)
        print(f"\n❌ Fehler: {e.error.error_message}")
        print(f"   Typ: {e.error.error_type}")
        print(f"   Buch ID: {e.error_data.book_id}")
    except Exception as e:
        logger.error(f"Unerwarteter Testfehler: {e}", exc_info=True)
        print(f"\n❌ Unerwarteter Fehler: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TESTS ABGESCHLOSSEN")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())