#!/usr/bin/env python3
"""
Test Script für OpenLibrary API Integration und Multi-Source Data Fusion System.
Testet die neue erweiterte Buchidentifikation mit verschiedenen Szenarien.
"""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from shared.apis.openlibrary import OpenLibraryClient
from shared.apis.data_fusion import DataFusionEngine, fuse_book_data_from_sources

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test-Daten für verschiedene Szenarien
TEST_CASES = [
    {
        "name": "ISBN_Perfect_Match",
        "description": "Test mit perfektem ISBN-Match",
        "base_data": {
            "isbn": "9780316769174",
            "title": "The Catcher in the Rye",
            "author": "J.D. Salinger",
            "condition": "Sehr gut"
        }
    },
    {
        "name": "Title_Author_Match", 
        "description": "Test mit Titel+Autor ohne ISBN",
        "base_data": {
            "title": "Harry Potter and the Philosopher's Stone",
            "author": "J.K. Rowling",
            "condition": "Gut"
        }
    },
    {
        "name": "German_Book",
        "description": "Test mit deutschem Buch",
        "base_data": {
            "isbn": "9783423282388", 
            "title": "Der Gesang der Flusskrebse",
            "author": "Delia Owens",
            "condition": "Wie neu"
        }
    },
    {
        "name": "Fuzzy_Search",
        "description": "Test mit ungenauen Daten",
        "base_data": {
            "title": "1984",
            "author": "George Orwell",
            "condition": "Akzeptabel"
        }
    },
    {
        "name": "No_Match",
        "description": "Test mit nicht existierendem Buch",
        "base_data": {
            "title": "Completely Fictional Book That Does Not Exist",
            "author": "Nonexistent Author",
            "condition": "Gut"
        }
    }
]

class MultiSourceTester:
    """Test-Klasse für Multi-Source Integration."""
    
    def __init__(self):
        self.openlibrary_client = OpenLibraryClient()
        self.fusion_engine = DataFusionEngine()
        self.results = []
    
    async def test_openlibrary_basic(self):
        """Test der grundlegenden OpenLibrary API-Funktionalität."""
        logger.info("=== Testing OpenLibrary Basic Functionality ===")
        
        # Test ISBN-Suche
        logger.info("Testing ISBN search...")
        isbn_result = self.openlibrary_client.search_by_isbn("9780316769174")
        if isbn_result:
            logger.info(f"✓ ISBN search successful: {isbn_result.title} by {', '.join(isbn_result.authors or [])}")
        else:
            logger.warning("✗ ISBN search failed")
        
        # Test Titel+Autor Suche
        logger.info("Testing title+author search...")
        title_results = self.openlibrary_client.search_by_title_author("1984", "George Orwell")
        if title_results:
            logger.info(f"✓ Title+Author search successful: Found {len(title_results)} results")
            for i, result in enumerate(title_results[:2]):
                logger.info(f"  Result {i+1}: {result.title} (confidence: {result.confidence_score:.2f})")
        else:
            logger.warning("✗ Title+Author search failed")
        
        return {"isbn_result": isbn_result, "title_results": title_results}
    
    async def test_data_fusion_scenarios(self):
        """Test der Data Fusion Engine mit verschiedenen Szenarien."""
        logger.info("=== Testing Data Fusion Scenarios ===")
        
        for test_case in TEST_CASES:
            logger.info(f"\nTesting: {test_case['name']} - {test_case['description']}")
            
            try:
                # Simuliere Basis-Daten
                base_data = test_case["base_data"]
                
                # Führe Data Fusion durch
                start_time = asyncio.get_event_loop().time()
                fused_data = await self.fusion_engine.fuse_book_data(
                    base_data=base_data,
                    enable_parallel=True
                )
                end_time = asyncio.get_event_loop().time()
                
                # Sammle Ergebnisse
                result = {
                    "test_case": test_case["name"],
                    "success": True,
                    "duration": round(end_time - start_time, 2),
                    "title": fused_data.title,
                    "authors": fused_data.authors,
                    "isbn": fused_data.isbn,
                    "confidence": fused_data.overall_confidence,
                    "quality_score": fused_data.quality_score,
                    "sources_used": fused_data.sources_used,
                    "search_methods": fused_data.search_methods,
                    "fusion_strategy": fused_data.fusion_strategy
                }
                
                self.results.append(result)
                
                # Log Ergebnisse
                logger.info(f"✓ Success in {result['duration']}s")
                logger.info(f"  Title: {result['title']}")
                logger.info(f"  Authors: {result['authors']}")
                logger.info(f"  Confidence: {result['confidence']:.2f}")
                logger.info(f"  Quality: {result['quality_score']:.2f}")
                logger.info(f"  Sources: {result['sources_used']}")
                logger.info(f"  Methods: {result['search_methods']}")
                
            except Exception as e:
                logger.error(f"✗ Test failed: {e}")
                self.results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
    
    async def test_parallel_vs_sequential(self):
        """Vergleicht parallele vs. sequentielle Verarbeitung."""
        logger.info("=== Testing Parallel vs Sequential Processing ===")
        
        test_data = {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "isbn": "9780743273565"
        }
        
        # Test parallel processing
        logger.info("Testing parallel processing...")
        start_time = asyncio.get_event_loop().time()
        parallel_result = await self.fusion_engine.fuse_book_data(
            base_data=test_data,
            enable_parallel=True
        )
        parallel_time = asyncio.get_event_loop().time() - start_time
        
        # Test sequential processing
        logger.info("Testing sequential processing...")
        start_time = asyncio.get_event_loop().time()
        sequential_result = await self.fusion_engine.fuse_book_data(
            base_data=test_data,
            enable_parallel=False
        )
        sequential_time = asyncio.get_event_loop().time() - start_time
        
        # Vergleiche Ergebnisse
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        logger.info(f"Parallel processing: {parallel_time:.2f}s")
        logger.info(f"Sequential processing: {sequential_time:.2f}s") 
        logger.info(f"Speedup: {speedup:.2f}x")
        
        return {
            "parallel_time": parallel_time,
            "sequential_time": sequential_time,
            "speedup": speedup,
            "parallel_confidence": parallel_result.overall_confidence,
            "sequential_confidence": sequential_result.overall_confidence
        }
    
    async def test_caching_functionality(self):
        """Test der Caching-Funktionalität."""
        logger.info("=== Testing Caching Functionality ===")
        
        test_data = {
            "isbn": "9780452284234",
            "title": "Nineteen Eighty-Four",
            "author": "George Orwell"
        }
        
        # Erster Aufruf (ohne Cache)
        logger.info("First call (no cache)...")
        start_time = asyncio.get_event_loop().time()
        first_result = await self.fusion_engine.fuse_book_data(base_data=test_data)
        first_time = asyncio.get_event_loop().time() - start_time
        
        # Zweiter Aufruf (mit Cache)
        logger.info("Second call (with cache)...")
        start_time = asyncio.get_event_loop().time()
        second_result = await self.fusion_engine.fuse_book_data(base_data=test_data)
        second_time = asyncio.get_event_loop().time() - start_time
        
        cache_speedup = first_time / second_time if second_time > 0 else 0
        
        logger.info(f"First call: {first_time:.2f}s")
        logger.info(f"Second call: {second_time:.2f}s")
        logger.info(f"Cache speedup: {cache_speedup:.2f}x")
        
        return {
            "first_call_time": first_time,
            "second_call_time": second_time,
            "cache_speedup": cache_speedup,
            "results_identical": first_result.title == second_result.title
        }
    
    def generate_report(self):
        """Generiert einen Testbericht."""
        logger.info("=== Test Report ===")
        
        successful_tests = len([r for r in self.results if r.get("success", False)])
        total_tests = len(self.results)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        # Analysiere Konfidenz-Scores
        confidences = [r["confidence"] for r in self.results if r.get("success") and "confidence" in r]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            logger.info(f"Average Confidence: {avg_confidence:.2f}")
        
        # Analysiere Quellen-Usage
        sources_usage = {}
        for result in self.results:
            if result.get("success") and "sources_used" in result:
                for source in result["sources_used"]:
                    sources_usage[source] = sources_usage.get(source, 0) + 1
        
        logger.info(f"Sources Usage: {sources_usage}")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests/total_tests*100 if total_tests > 0 else 0,
            "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "sources_usage": sources_usage,
            "detailed_results": self.results
        }

async def main():
    """Hauptfunktion für Tests."""
    logger.info("Starting Multi-Source Integration Tests...")
    
    tester = MultiSourceTester()
    
    try:
        # Test 1: OpenLibrary Basic Functionality
        await tester.test_openlibrary_basic()
        
        # Test 2: Data Fusion Scenarios
        await tester.test_data_fusion_scenarios()
        
        # Test 3: Performance Tests
        performance_results = await tester.test_parallel_vs_sequential()
        
        # Test 4: Caching Tests
        cache_results = await tester.test_caching_functionality()
        
        # Generate Final Report
        final_report = tester.generate_report()
        
        # Save results to file
        test_results = {
            "performance": performance_results,
            "caching": cache_results,
            "final_report": final_report
        }
        
        with open("multisource_integration_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        logger.info("Tests completed successfully!")
        logger.info("Results saved to: multisource_integration_test_results.json")
        
        return test_results
        
    except Exception as e:
        logger.error(f"Tests failed with error: {e}")
        raise

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("ENABLE_OPENLIBRARY", "true")
    os.environ.setdefault("ENABLE_PARALLEL_APIS", "true") 
    os.environ.setdefault("USE_ENHANCED_RESEARCH", "true")
    
    try:
        results = asyncio.run(main())
        print("\n✓ Multi-Source Integration Tests completed successfully!")
        print(f"Success Rate: {results['final_report']['success_rate']:.1f}%")
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\n✗ Tests failed: {e}")
        sys.exit(1)