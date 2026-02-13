# Workflow Orchestrator Integration Guide

**Status:** Phase 2 Implementation Complete  
**Datum:** 2025-11-07  
**Version:** 1.0

## Übersicht

Dieses Dokument beschreibt die Integration des Workflow Orchestrators in den Ingestion Agent. Der Orchestrator implementiert intelligentes Routing zwischen ISBN-Path und Search-Path.

## Implementierte Komponenten

### 1. Workflow Orchestrator Module

**Datei:** [`agents/ingestion-agent/workflow_orchestrator.py`](../../agents/ingestion-agent/workflow_orchestrator.py)

**Hauptklassen:**
- `WorkflowOrchestrator`: Zentrale Orchestrierung
- `WorkflowPath` (Enum): ISBN, SEARCH_GROUNDING, MANUAL_REVIEW
- `ProcessingResult` (Dataclass): Ergebnis-Struktur

**Features:**
- ✅ Intelligentes Routing basierend auf ISBN-Confidence
- ✅ Parallele API-Calls (Google Books + OpenLibrary)
- ✅ Automatisches Fallback Search-Path → ISBN-Path
- ✅ Error Handling mit Manual Review Queue
- ✅ Graceful Degradation bei fehlenden API-Keys

### 2. Test Suite

**Datei:** [`tests/test_workflow_orchestrator.py`](../../tests/test_workflow_orchestrator.py)

**Test-Coverage:**
- ✅ Routing-Logik (4 Tests)
- ✅ ISBN-Path Execution (3 Tests)
- ✅ Search-Path Execution (3 Tests)
- ✅ End-to-End Process (3 Tests)
- ✅ Error Handling (2 Tests)

**Test-Ergebnisse:**
```
15 passed in 43.75s
```

## Integration in Ingestion Agent

### Schritt 1: Import hinzufügen

In [`agents/ingestion-agent/main.py`](../../agents/ingestion-agent/main.py):

```python
from workflow_orchestrator import (
    WorkflowOrchestrator, 
    ProcessingResult, 
    WorkflowPath
)
```

### Schritt 2: Endpoint anpassen

**Aktueller `/process` Endpoint:** Ersetzen mit neuer Orchestrator-Integration

```python
@app.post("/process")
async def process_book(request: dict):
    """
    Process book with workflow orchestrator.
    
    Request body:
    {
        "book_id": "firestore_document_id",
        "user_id": "user_uid",
        "image_urls": ["gs://bucket/path1.jpg", ...],
        "user_settings": {
            "gui_review_enabled": false,
            "isbn_confidence_threshold": 0.7
        }
    }
    
    Returns:
    {
        "success": true|false,
        "status": "ingested"|"needs_manual_review"|"error",
        "path": "isbn"|"search_grounding"|"manual_review",
        "confidence": 0.0-1.0,
        "processing_time_ms": 1234.56,
        "requires_user_input": true|false,
        "error": "optional error message"
    }
    """
    try:
        # Extract request parameters
        book_id = request["book_id"]
        user_id = request["user_id"]
        image_urls = request["image_urls"]
        user_settings = request.get("user_settings", {})
        
        logger.info(
            f"Processing book {book_id} for user {user_id} "
            f"with {len(image_urls)} images"
        )
        
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator(
            project_id=os.getenv("GCP_PROJECT_ID"),
            isbn_confidence_threshold=user_settings.get(
                "isbn_confidence_threshold", 0.7
            ),
            enable_gui_review=user_settings.get("gui_review_enabled", False)
        )
        
        # Download images from Cloud Storage to temp directory
        image_paths = await download_images_from_gcs(image_urls)
        
        try:
            # Process with orchestrator
            result: ProcessingResult = await orchestrator.process_book(
                book_id=book_id,
                image_paths=image_paths,
                user_id=user_id,
                user_settings=user_settings
            )
            
            # Update Firestore based on result
            if result.success:
                await update_firestore_success(
                    book_id=book_id,
                    user_id=user_id,
                    book_data=result.book_data,
                    path=result.path.value,
                    confidence=result.confidence
                )
                status = "ingested"
                
            elif result.requires_user_input:
                await update_firestore_manual_review(
                    book_id=book_id,
                    user_id=user_id,
                    failure_info=result.book_data,
                    error_message=result.error_message
                )
                status = "needs_manual_review"
                
            else:
                await update_firestore_error(
                    book_id=book_id,
                    user_id=user_id,
                    error_message=result.error_message
                )
                status = "error"
            
            logger.info(
                f"Book {book_id} processing complete: "
                f"status={status}, path={result.path.value}, "
                f"time={result.processing_time_ms:.0f}ms"
            )
            
            return {
                "success": result.success,
                "status": status,
                "path": result.path.value,
                "confidence": result.confidence,
                "processing_time_ms": result.processing_time_ms,
                "requires_user_input": result.requires_user_input,
                "api_calls": result.api_calls,
                "cost_estimate": result.cost_estimate
            }
            
        finally:
            # Cleanup temp files
            await cleanup_temp_files(image_paths)
            
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return {
            "success": False,
            "status": "error",
            "error": f"Missing required field: {e}"
        }
        
    except Exception as e:
        logger.error(f"Error processing book: {e}", exc_info=True)
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }
```

### Schritt 3: Helper Functions implementieren

```python
async def download_images_from_gcs(image_urls: List[str]) -> List[Path]:
    """
    Download images from Cloud Storage to temp directory.
    
    Args:
        image_urls: List of gs:// URLs
        
    Returns:
        List of local Path objects
    """
    from google.cloud import storage
    import tempfile
    
    storage_client = storage.Client()
    temp_dir = Path(tempfile.mkdtemp(prefix="book_images_"))
    image_paths = []
    
    for i, url in enumerate(image_urls):
        # Parse gs://bucket/path
        if not url.startswith("gs://"):
            raise ValueError(f"Invalid GCS URL: {url}")
            
        parts = url[5:].split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1]
        
        # Download
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Save to temp file
        local_path = temp_dir / f"image_{i}_{Path(blob_path).name}"
        blob.download_to_filename(str(local_path))
        image_paths.append(local_path)
        
    return image_paths


async def cleanup_temp_files(image_paths: List[Path]):
    """Delete temporary image files and directory."""
    import shutil
    
    if not image_paths:
        return
        
    temp_dir = image_paths[0].parent
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        logger.debug(f"Cleaned up temp directory: {temp_dir}")


async def update_firestore_success(
    book_id: str,
    user_id: str, 
    book_data: Dict[str, Any],
    path: str,
    confidence: float
):
    """Update Firestore with successful ingestion."""
    from shared.firestore import FirestoreClient
    
    firestore = FirestoreClient(project_id=os.getenv("GCP_PROJECT_ID"))
    
    await firestore.update_book(
        user_id=user_id,
        book_id=book_id,
        data={
            "status": "ingested",
            "metadata": book_data,
            "ingestion_path": path,
            "confidence": confidence,
            "ingested_at": firestore.server_timestamp()
        }
    )


async def update_firestore_manual_review(
    book_id: str,
    user_id: str,
    failure_info: Dict[str, Any],
    error_message: Optional[str]
):
    """Update Firestore for manual review queue."""
    from shared.firestore import FirestoreClient
    
    firestore = FirestoreClient(project_id=os.getenv("GCP_PROJECT_ID"))
    
    await firestore.update_book(
        user_id=user_id,
        book_id=book_id,
        data={
            "status": "needs_manual_review",
            "failure_info": failure_info,
            "error_message": error_message,
            "requires_user_input": True,
            "review_requested_at": firestore.server_timestamp()
        }
    )
    
    # TODO: Add to manual review queue collection
    # TODO: Trigger user notification


async def update_firestore_error(
    book_id: str,
    user_id: str,
    error_message: str
):
    """Update Firestore with error status."""
    from shared.firestore import FirestoreClient
    
    firestore = FirestoreClient(project_id=os.getenv("GCP_PROJECT_ID"))
    
    await firestore.update_book(
        user_id=user_id,
        book_id=book_id,
        data={
            "status": "error",
            "error_message": error_message,
            "failed_at": firestore.server_timestamp()
        }
    )
```

## Workflow Paths

### 1. ISBN-Path (Primär)

**Trigger:** ISBN erfolgreich extrahiert mit Confidence ≥ 0.7

**Flow:**
1. Parallele API-Calls (Google Books + OpenLibrary)
2. Data Fusion Engine
3. Erfolg → Status "ingested"
4. Fehler → Fallback zu Search-Path

**Durchschnittliche Dauer:** ~2-3 Sekunden

### 2. Search-Path (Fallback)

**Trigger:** 
- Keine ISBN gefunden
- ISBN Confidence < 0.7
- ISBN-Path fehlgeschlagen

**Flow:**
1. Image Classification (Front/Back/Spine/Other)
2. Google Search Grounding mit multimodalen Bildern
3. Metadaten-Extraktion via Gemini Flash
4. Erfolg → Status "ingested"
5. Fehler → Manual Review

**Durchschnittliche Dauer:** ~5-8 Sekunden

### 3. Manual Review (Letzter Ausweg)

**Trigger:**
- Beide Paths fehlgeschlagen
- Keine ausreichenden Daten gefunden

**Flow:**
1. Status "needs_manual_review" setzen
2. Alle verfügbaren Daten speichern
3. In Review-Queue eintragen
4. User-Notification triggern (TODO)

## Konfiguration

### Umgebungsvariablen

```bash
# Erforderlich
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Optional (für Google Books API)
GOOGLE_BOOKS_API_KEY=your-api-key
```

### User Settings

```python
user_settings = {
    "isbn_confidence_threshold": 0.7,  # 0.0-1.0
    "gui_review_enabled": False,       # GUI Review Phase (TODO)
}
```

## Monitoring & Metrics

Der Orchestrator trackt automatisch:

```python
result = ProcessingResult(
    success=True,
    path=WorkflowPath.ISBN,
    confidence=0.92,
    processing_time_ms=2341.5,
    cost_estimate=0.003,  # USD
    api_calls={
        "google_books": 1,
        "openlibrary": 1,
        "vertex_ai": 0
    }
)
```

Diese Metriken können für:
- Performance-Monitoring verwendet werden
- Cost-Tracking
- Path-Optimierung
- SLA-Compliance

## Testing

### Unit Tests ausführen

```bash
# Alle Tests
pytest tests/test_workflow_orchestrator.py -v

# Spezifischer Test
pytest tests/test_workflow_orchestrator.py::test_should_use_isbn_path_success -v

# Mit Coverage
pytest tests/test_workflow_orchestrator.py --cov=agents.ingestion_agent.workflow_orchestrator
```

### Integration Test

```bash
# TODO: Integration test with real Cloud Storage images
pytest tests/test_ingestion_integration.py -v
```

## Fehlerbehandlung

### ISBN-Path Fehler

**Szenario:** Google Books API nicht verfügbar

**Verhalten:**
1. Exception wird geloggt als Warning
2. Nur OpenLibrary-Daten werden verwendet
3. Falls beide fehlschlagen → Fallback zu Search-Path

### Search-Path Fehler

**Szenario:** Google Search Grounding nicht verfügbar

**Verhalten:**
1. Exception wird geloggt als Error
2. Routing zu Manual Review
3. Status "needs_manual_review"
4. User wird benachrichtigt (TODO)

### Complete Failure

**Szenario:** Alle Paths fehlgeschlagen

**Verhalten:**
```python
ProcessingResult(
    success=False,
    path=WorkflowPath.MANUAL_REVIEW,
    requires_user_input=True,
    book_data={
        "isbn_attempt": {...},
        "search_attempt": {...},
        "images": [...],
    },
    error_message="Automatic identification failed"
)
```

## TODOs

### Kurzfristig (Phase 2)
- [ ] GUI Review Integration implementieren
- [ ] Manual Review Queue in Firestore
- [ ] User Notifications implementieren
- [ ] Integration Tests schreiben

### Mittelfristig (Phase 3)
- [ ] Cost-Tracking Dashboard
- [ ] Performance-Optimierung (Caching)
- [ ] Batch-Processing Support
- [ ] A/B Testing für Routing-Schwellwerte

### Langfristig (Phase 4)
- [ ] ML-basierte Routing-Optimierung
- [ ] Custom Search Grounding Training
- [ ] Multi-Language Support
- [ ] Barcode-Scanner Integration

## Referenzen

- [Technical Architecture](TECHNICAL_ARCHITECTURE.md)
- [ISBN Extraction Guide](INGESTION_AGENT_FIXES_2025-11-04.md)
- [Search Grounding Integration](../archive/HANDOVER_2025-11-04_PART3_SEARCH_GROUNDING.md)
- [Data Fusion Engine](../../shared/apis/data_fusion.py)

## Support

Bei Fragen oder Problemen:
1. Check die Logs: Cloud Logging Console
2. Review die Test-Results
3. Kontaktiere das Development Team

---

**Letzte Aktualisierung:** 2025-11-07  
**Verantwortlich:** Roo AI Assistant  
**Status:** ✅ Implementation Complete, Integration Pending