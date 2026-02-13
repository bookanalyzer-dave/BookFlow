"""
Real-World Book Testing Script - Workflow Orchestrator
Tests die neue Buch-Erkennungspipeline mit intelligentem Routing
"""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
import re
from dotenv import load_dotenv

load_dotenv()

# Add agents/ingestion-agent to path for import
import sys
sys.path.insert(0, str(Path(__file__).parent / "agents" / "ingestion-agent"))

from workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowPath,
    ProcessingResult
)
from shared.isbn import ISBNExtractor
from shared.monitoring import get_logger, get_metrics_collector
from shared.image_sorter import ImageSorterAgent, ImageReviewGUI


class RealWorldBookTester:
    """Tests die neue Workflow Orchestrator Pipeline"""
    
    KNOWN_LABELS = ["cover", "spine", "back", "isbn", "pages", "inside"]
    
    def __init__(self, image_dir: str = "test_books", use_sorter: bool = False):
        self.image_dir = Path(image_dir)
        self.test_dir = Path(image_dir)  # Alias for compatibility
        self.use_sorter = use_sorter  # True = nutze Image Sorter Agent
        self.logger = get_logger("real_world_test")
        self.metrics = get_metrics_collector("real_world_test")
        
        # New architecture components
        project_id = os.getenv("GCP_PROJECT_ID", "project-52b2fab8-15a1-4b66-9f3")
        self.orchestrator = WorkflowOrchestrator(
            project_id=project_id,
            isbn_confidence_threshold=0.7,
            enable_gui_review=False
        )
        
        self.isbn_extractor = ISBNExtractor(
            confidence_threshold=0.7
        )
        
        # Initialize Image Sorter if enabled
        if self.use_sorter:
            if not project_id:
                print("⚠️  GCP_PROJECT_ID nicht gesetzt, Image Sorter deaktiviert")
                self.use_sorter = False
                self.sorter = None
            else:
                self.sorter = ImageSorterAgent()
        else:
            self.sorter = None
        
        self.results = []
    
    def check_prerequisites(self) -> bool:
        """Prüft ob alle Voraussetzungen erfüllt sind"""
        print("\n" + "="*80)
        print("🔍 VORAUSSETZUNGEN PRÜFEN")
        print("="*80)
        
        checks = []
        
        # Check 1: Image Directory
        if self.image_dir.exists():
            images = list(self.image_dir.glob("*.jpg")) + list(self.image_dir.glob("*.png"))
            print(f"✅ Bild-Verzeichnis gefunden: {self.image_dir}")
            print(f"   📸 {len(images)} Bilder gefunden")
            checks.append(len(images) > 0)
        else:
            print(f"❌ Bild-Verzeichnis nicht gefunden: {self.image_dir}")
            print(f"   Bitte erstelle das Verzeichnis und lege Buchfotos hinein.")
            checks.append(False)
        
        # Check 2: GCP Project ID
        project_id = os.getenv("GCP_PROJECT_ID")
        if project_id:
            print(f"✅ GCP_PROJECT_ID gesetzt: {project_id}")
            checks.append(True)
        else:
            print(f"⚠️  GCP_PROJECT_ID nicht gesetzt, verwende Default")
            checks.append(True)  # Not critical, we have default
        
        # Check 3: Workflow Orchestrator
        print(f"✅ Workflow Orchestrator initialisiert")
        print(f"   • ISBN Confidence Threshold: 0.7")
        print(f"   • Intelligentes Routing aktiv")
        
        print("\n" + "="*80)
        critical_checks = checks[0]  # Only image directory is critical
        if critical_checks:
            print("✅ Kritische Voraussetzungen erfüllt - Tests können durchgeführt werden")
            return True
        else:
            print("❌ Kritische Voraussetzungen nicht erfüllt")
            return False
    
    def _group_images_simple(self, images: List[Path]) -> Dict[str, List[Path]]:
        """Simple grouping: Extract prefix before number."""
        groups = {}
        for img in images:
            # Extract base name (e.g., "IMG" from "IMG_2261.jpg" or "Buch" from "Buch.jpg")
            name = img.stem
            
            # Remove trailing numbers/underscores
            base = re.sub(r'[_\-]?\d+$', '', name) or name
            
            if base not in groups:
                groups[base] = []
            groups[base].append(img)
        
        return groups
    
    async def test_single_book(self, images: List[Path], book_name: str):
        """Test single book with new Workflow Orchestrator."""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"📚 TESTE BUCH: {book_name}")
        self.logger.info(f"{'='*80}\n")
        
        # Display images
        self.logger.info(f"📸 Bilder ({len(images)}):")
        for img in images:
            self.logger.info(f"   • {img.name}")
        
        try:
            # Generate book_id for testing
            book_id = f"test-{book_name.lower()}-{int(time.time())}"
            user_id = "test-user"
            
            # Process with Workflow Orchestrator
            self.logger.info("\n🚀 Verarbeite mit Workflow Orchestrator...")
            
            result = await self.orchestrator.process_book(
                book_id=book_id,
                image_paths=images,
                user_id=user_id,
                user_settings={}
            )
            
            # Display results
            self.logger.info(f"\n{'='*80}")
            self.logger.info("📊 ERGEBNIS")
            self.logger.info(f"{'='*80}")
            self.logger.info(f"✅ Erfolg: {result.success}")
            self.logger.info(f"🛤️  Pfad: {result.path.value}")
            self.logger.info(f"📈 Konfidenz: {result.confidence:.2%}")
            self.logger.info(f"⏱️  Verarbeitung: {result.processing_time_ms:.0f}ms")
            
            if result.success and result.book_data:
                self.logger.info(f"\n📖 Buch-Daten:")
                self.logger.info(f"   📝 Titel: {result.book_data.get('title', 'N/A')}")
                self.logger.info(f"   👤 Autor(en): {', '.join(result.book_data.get('authors', ['N/A']))}")
                self.logger.info(f"   📚 ISBN: {result.book_data.get('isbn', 'N/A')}")
                self.logger.info(f"   📅 Jahr: {result.book_data.get('published_date', 'N/A')}")
                if result.book_data.get('publisher'):
                    self.logger.info(f"   🏢 Verlag: {result.book_data.get('publisher')}")
            
            elif result.requires_user_input:
                self.logger.info(f"\n⚠️  Manuelle Überprüfung erforderlich:")
                self.logger.info(f"   Grund: {result.error_message}")
                if result.book_data:
                    isbn_attempt = result.book_data.get('isbn_attempt', {})
                    self.logger.info(f"   ISBN-Versuch: {isbn_attempt.get('found', False)}")
                    if isbn_attempt.get('isbn'):
                        self.logger.info(f"   Gefundene ISBN: {isbn_attempt['isbn']} (Konfidenz: {isbn_attempt.get('confidence', 0):.2%})")
            
            else:
                self.logger.info(f"\n❌ Fehler: {result.error_message}")
            
            # API Call statistics
            if result.api_calls:
                self.logger.info(f"\n📞 API-Aufrufe:")
                for api, count in result.api_calls.items():
                    self.logger.info(f"   • {api}: {count}")
            
            # Store result for summary
            self.results.append({
                "book": book_name,
                "success": result.success,
                "path": result.path.value,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms,
                "requires_user_input": result.requires_user_input,
                "book_data": result.book_data,
                "api_calls": result.api_calls
            })
            
        except Exception as e:
            self.logger.error(f"\n❌ Fehler beim Testen von {book_name}: {e}")
            self.results.append({
                "book": book_name,
                "success": False,
                "error": str(e)
            })
    
    async def run_all_tests(self):
        """Run all tests with new architecture."""
        if not self.check_prerequisites():
            return
        
        # Discover images
        all_images = list(self.test_dir.glob("*.jpg")) + list(self.test_dir.glob("*.png"))
        
        if not all_images:
            self.logger.error("❌ Keine Testbilder gefunden")
            return
        
        # Use Image Sorter if enabled
        if self.use_sorter and self.sorter:
            print("\n" + "="*80)
            print("🤖 IMAGE SORTER AGENT")
            print("="*80)
            print(f"\n📸 Analysiere {len(all_images)} Bilder mit Gemini Flash...")
            
            try:
                # Classify images
                classifications = await self.sorter.classify_batch(all_images)
                
                # Show classification summary
                print(f"\n✅ Klassifikation abgeschlossen:")
                label_counts = {}
                for cls in classifications:
                    label = cls["label"]
                    label_counts[label] = label_counts.get(label, 0) + 1
                for label, count in sorted(label_counts.items()):
                    print(f"   • {label}: {count}")
                
                # Cluster by book
                clustered_books = self.sorter.cluster_by_book(classifications)
                print(f"\n📚 {len(clustered_books)} Buch(er) erkannt")
                for book_name, images in clustered_books.items():
                    print(f"   • {book_name}: {len(images)} Bilder")
                
                # Generate new filenames
                filename_mapping = self.sorter.generate_new_filenames(clustered_books)
                
                # Show GUI for confirmation and editing
                print("\n🖼️  Öffne GUI zur Review & Bearbeitung...")
                print("   ✏️  Du kannst Labels und Buch-Zuordnungen ändern")
                gui = ImageReviewGUI(filename_mapping, self.image_dir)
                confirmed, modified_mapping = gui.show()
                
                if not confirmed or not modified_mapping:
                    print("\n❌ Abgebrochen durch Benutzer")
                    return
                
                # Use modified mapping (with user changes)
                filename_mapping = modified_mapping
                print("\n✅ Änderungen vom Benutzer übernommen")
                
                # Rename files
                print("\n📝 Benenne Dateien um...")
                for orig_path, mapping in filename_mapping.items():
                    new_path = self.image_dir / mapping["new_name"]
                    Path(orig_path).rename(new_path)
                    print(f"   ✅ {Path(orig_path).name} → {mapping['new_name']}")
                
                print("\n✅ Image Sorter abgeschlossen")
                
                # Refresh image list after renaming
                all_images = list(self.test_dir.glob("*.jpg")) + list(self.test_dir.glob("*.png"))
                
            except Exception as e:
                print(f"\n⚠️  Image Sorter Fehler: {e}")
                print("   Fahre mit manueller Gruppierung fort...")
                self.logger.log_error("image_sorter", e, {})
        
        # Simple grouping by filename prefix
        book_groups = self._group_images_simple(all_images)
        
        self.logger.info(f"\n📚 Gefundene Bücher: {len(book_groups)}")
        for book_name, images in book_groups.items():
            self.logger.info(f"   • {book_name}: {len(images)} Bilder")
        
        # Test each book
        for book_name, images in book_groups.items():
            await self.test_single_book(images, book_name)
            self.logger.info("\n" + "="*80 + "\n")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        self.logger.info("\n" + "="*80)
        self.logger.info("📊 TEST ZUSAMMENFASSUNG")
        self.logger.info("="*80)
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success"))
        manual_review = sum(1 for r in self.results if r.get("requires_user_input"))
        failed = total - successful - manual_review
        
        # Path statistics
        isbn_path = sum(1 for r in self.results if r.get("path") == "isbn")
        search_path = sum(1 for r in self.results if r.get("path") == "search_grounding")
        manual_path = sum(1 for r in self.results if r.get("path") == "manual_review")
        
        self.logger.info(f"\n📈 Statistiken:")
        self.logger.info(f"   Gesamt: {total}")
        self.logger.info(f"   ✅ Erfolgreich: {successful} ({successful/total*100:.1f}%)")
        self.logger.info(f"   ⚠️  Manuelle Review: {manual_review} ({manual_review/total*100:.1f}%)")
        self.logger.info(f"   ❌ Fehlgeschlagen: {failed} ({failed/total*100:.1f}%)")
        
        self.logger.info(f"\n🛤️ Routing:")
        self.logger.info(f"   ISBN-Path: {isbn_path}")
        self.logger.info(f"   Search-Path: {search_path}")
        self.logger.info(f"   Manual-Review: {manual_path}")
        
        # Average processing time
        avg_time = sum(r.get("processing_time_ms", 0) for r in self.results) / total if total > 0 else 0
        self.logger.info(f"\n⏱️  Durchschnittliche Verarbeitung: {avg_time:.0f}ms")
        
        # Detailed results
        self.logger.info(f"\n📚 Detaillierte Ergebnisse:")
        for result in self.results:
            status = "✅" if result.get("success") else "⚠️" if result.get("requires_user_input") else "❌"
            book = result.get("book", "Unknown")
            path = result.get("path", "N/A")
            confidence = result.get("confidence", 0)
            
            self.logger.info(f"   {status} {book}: {path} (Konfidenz: {confidence:.2%})")
        
        # Save detailed report
        report_file = f"real_world_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_books": total,
                    "successful": successful,
                    "manual_review": manual_review,
                    "failed": failed,
                    "isbn_path_count": isbn_path,
                    "search_path_count": search_path,
                    "manual_review_count": manual_path,
                    "avg_processing_time_ms": avg_time
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n📄 Detaillierter Bericht gespeichert: {report_file}")
        
        # Save metrics
        self.metrics.save_report()
        self.logger.info(f"📊 Metriken gespeichert")


async def main():
    """Main entry point."""
    print("="*80)
    print("📚 REAL-WORLD BOOK TESTING - Workflow Orchestrator")
    print("="*80)
    print("\nDieses Script testet die neue Buch-Erkennungspipeline mit:")
    print("• ISBN Extractor (Gemini Flash)")
    print("• Intelligentes Routing (ISBN-Path vs. Search-Path)")
    print("• Automatisches Fallback-Handling")
    print("• Manual Review für komplexe Fälle")
    print("\n" + "="*80)
    
    # Ask if user wants Image Sorter
    print("\nMöchtest du den Image Sorter Agent verwenden?")
    print("  [1] Nein - Bilder manuell benennen")
    print("  [2] Ja - AI-automatische Klassifikation & Benennung")
    choice = input("Wahl (1/2): ").strip()
    use_sorter = choice == "2"
    
    if use_sorter:
        print("\n🤖 Image Sorter Agent wird aktiviert:")
        print("   • Nutzt Gemini Flash für automatische Klassifikation")
        print("   • ✨ GUI mit Bearbeitungs-Möglichkeiten")
        print("   • Benötigt GCP_PROJECT_ID")
    
    print("\nDrücke Enter um zu starten...")
    input()
    
    tester = RealWorldBookTester(use_sorter=use_sorter)
    await tester.run_all_tests()
    
    print("\n" + "="*80)
    print("✅ TESTS ABGESCHLOSSEN")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
