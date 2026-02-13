"""
Test Script für Image Sorter Agent
Testet die automatische Klassifikation und Gruppierung von Buchfotos
"""

import asyncio
import os
from pathlib import Path
from shared.image_sorter import ImageSorterAgent, ImageReviewGUI


async def test_classifier():
    """Testet den Image Sorter Agent mit Beispielbildern"""
    print("="*80)
    print("🤖 IMAGE SORTER AGENT TEST")
    print("="*80)
    
    # Check prerequisites
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("\n❌ GCP_PROJECT_ID nicht gesetzt!")
        print("   Setze die Umgebungsvariable:")
        print("   export GCP_PROJECT_ID='your-project-id'")
        return
    
    print(f"\n✅ GCP Project ID: {project_id}")
    
    # Check test images
    test_dir = Path("test_books")
    if not test_dir.exists():
        print(f"\n❌ Test-Verzeichnis nicht gefunden: {test_dir}")
        print(f"   Erstelle das Verzeichnis und lege Testbilder hinein.")
        return
    
    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
        images.extend(list(test_dir.glob(ext)))
    
    if not images:
        print(f"\n❌ Keine Bilder im Test-Verzeichnis gefunden!")
        return
    
    print(f"\n📸 Gefundene Bilder: {len(images)}")
    for img in images[:5]:  # Show first 5
        print(f"   • {img.name}")
    if len(images) > 5:
        print(f"   ... und {len(images) - 5} weitere")
    
    # Initialize sorter
    print(f"\n🚀 Initialisiere Image Sorter Agent...")
    sorter = ImageSorterAgent(project_id=project_id, location="europe-west1")
    print(f"   ✅ Modell: gemini-1.5-flash-002")
    print(f"   ✅ Region: europe-west1")
    print(f"   ✅ Max Bilder: {sorter.max_images}")
    print(f"   ✅ Max Bücher: {sorter.max_books}")
    
    # Limit images for test
    if len(images) > sorter.max_images:
        print(f"\n⚠️  Zu viele Bilder ({len(images)}), limitiere auf {sorter.max_images}")
        images = images[:sorter.max_images]
    
    # PHASE 1: Classification
    print(f"\n" + "="*80)
    print(f"🔍 PHASE 1: KLASSIFIKATION")
    print(f"="*80)
    print(f"\nAnalysiere {len(images)} Bilder...")
    
    classifications = await sorter.classify_batch(images)
    
    print(f"\n✅ Klassifikation abgeschlossen!")
    print(f"\nErgebnisse:")
    for cls in classifications:
        confidence_emoji = "🟢" if cls["confidence"] >= 0.7 else "🟡" if cls["confidence"] >= 0.5 else "🔴"
        print(f"\n   📄 {Path(cls['path']).name}")
        print(f"      {confidence_emoji} Label: {cls['label']} (Confidence: {cls['confidence']:.0%})")
        print(f"      💭 Reasoning: {cls['reasoning'][:60]}...")
    
    # Statistics
    print(f"\n📊 Statistik:")
    label_counts = {}
    confidence_sum = 0
    for cls in classifications:
        label = cls["label"]
        label_counts[label] = label_counts.get(label, 0) + 1
        confidence_sum += cls["confidence"]
    
    for label, count in sorted(label_counts.items()):
        print(f"   • {label}: {count}")
    
    avg_confidence = confidence_sum / len(classifications) if classifications else 0
    print(f"   • Durchschnittliche Confidence: {avg_confidence:.0%}")
    
    # PHASE 2: Clustering
    print(f"\n" + "="*80)
    print(f"📚 PHASE 2: CLUSTERING")
    print(f"="*80)
    
    clustered_books = sorter.cluster_by_book(classifications)
    
    print(f"\n✅ {len(clustered_books)} Bücher erkannt:")
    for book_name, book_images in clustered_books.items():
        print(f"\n   📚 {book_name.upper()} ({len(book_images)} Bilder):")
        for img in book_images:
            print(f"      • {Path(img['path']).name} [{img['label']}]")
    
    # PHASE 3: Filename Generation
    print(f"\n" + "="*80)
    print(f"📝 PHASE 3: DATEINAMEN GENERIEREN")
    print(f"="*80)
    
    filename_mapping = sorter.generate_new_filenames(clustered_books)
    
    print(f"\n✅ Neue Dateinamen generiert:")
    for orig_path, mapping in filename_mapping.items():
        print(f"\n   {Path(orig_path).name}")
        print(f"   → {mapping['new_name']}")
        if mapping['confidence'] < 0.7:
            print(f"   ⚠️  Niedrige Confidence: {mapping['confidence']:.0%}")
    
    # PHASE 4: GUI Review (optional)
    print(f"\n" + "="*80)
    print(f"🖼️  PHASE 4: GUI REVIEW")
    print(f"="*80)
    
    show_gui = input("\nGUI zur Bestätigung anzeigen? (y/n): ").strip().lower()
    
    if show_gui == 'y':
        print("\n🖼️  Öffne GUI...")
        gui = ImageReviewGUI(filename_mapping, test_dir)
        confirmed = gui.show()
        
        if confirmed:
            print("\n✅ Benutzer hat bestätigt")
            
            # Ask if should rename
            do_rename = input("\nDateien wirklich umbenennen? (y/n): ").strip().lower()
            if do_rename == 'y':
                print("\n📝 Benenne Dateien um...")
                for orig_path, mapping in filename_mapping.items():
                    new_path = test_dir / mapping["new_name"]
                    Path(orig_path).rename(new_path)
                    print(f"   ✅ {Path(orig_path).name} → {mapping['new_name']}")
                print("\n✅ Umbenennung abgeschlossen")
            else:
                print("\n⏭️  Umbenennung übersprungen")
        else:
            print("\n❌ Benutzer hat abgebrochen")
    else:
        print("\n⏭️  GUI übersprungen")
    
    # Summary
    print(f"\n" + "="*80)
    print(f"✅ TEST ABGESCHLOSSEN")
    print(f"="*80)
    print(f"\n📊 Zusammenfassung:")
    print(f"   • Bilder analysiert: {len(classifications)}")
    print(f"   • Bücher erkannt: {len(clustered_books)}")
    print(f"   • Durchschnittliche Confidence: {avg_confidence:.0%}")
    print(f"   • Niedrige Confidence (<70%): {sum(1 for c in classifications if c['confidence'] < 0.7)}")


async def test_individual_image():
    """Testet die Klassifikation eines einzelnen Bildes"""
    print("="*80)
    print("🔍 EINZELBILD-TEST")
    print("="*80)
    
    # Check prerequisites
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("\n❌ GCP_PROJECT_ID nicht gesetzt!")
        return
    
    # Get image path
    image_path = input("\nBildpfad eingeben (relativ zu test_books/): ").strip()
    full_path = Path("test_books") / image_path
    
    if not full_path.exists():
        print(f"\n❌ Bild nicht gefunden: {full_path}")
        return
    
    print(f"\n📸 Analysiere: {full_path.name}")
    
    # Initialize sorter
    sorter = ImageSorterAgent(project_id=project_id)
    
    # Classify
    result = await sorter.classify_image(full_path)
    
    # Display result
    print(f"\n✅ Klassifikation:")
    print(f"   🏷️  Label: {result['label']}")
    print(f"   🎯 Confidence: {result['confidence']:.0%}")
    print(f"   💭 Reasoning: {result['reasoning']}")


async def main():
    print("\n🤖 Image Sorter Agent - Test Suite")
    print("\nWähle Test:")
    print("  [1] Vollständiger Test (alle Bilder in test_books/)")
    print("  [2] Einzelbild-Test (ein spezifisches Bild)")
    
    choice = input("\nWahl (1/2): ").strip()
    
    if choice == "1":
        await test_classifier()
    elif choice == "2":
        await test_individual_image()
    else:
        print("\n❌ Ungültige Wahl")


if __name__ == "__main__":
    asyncio.run(main())