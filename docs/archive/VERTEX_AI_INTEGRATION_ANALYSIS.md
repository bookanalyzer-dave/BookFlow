# 🚀 Vertex AI Integration - Analyse & Implementierungsstrategie

> Erweiterte Datenanreicherung für die Intelligent Book Sales Pipeline mit Vertex AI Services

---

## 📋 Executive Summary

**Ziel:** Erweitere die Data Fusion Engine mit intelligenten Vertex AI Services für präzisere Buchdaten

**Empfohlene Services:**
1. ✅ **Gemini-basierter Web Scraper** - Intelligentes Crawling von eurobuch.de, ZVAB, etc.
2. ⚠️ **Vertex AI Search** - Möglicherweise Overkill für unseren Use Case
3. ✅ **Grounding with Google Search** - Bessere Alternative zu Vertex AI Search

**Empfehlung:** Start mit **Gemini Web Scraper + Google Search Grounding**

---

## 🎯 Vertex AI Services im Detail

### 1. Gemini-basierter Web Scraper ⭐ EMPFOHLEN

**Was es ist:**
Intelligenter Crawler der mit Gemini 2.0 Flash Websites analysiert und strukturierte Daten extrahiert.

**Vorteile für unsere Pipeline:**
- ✅ Kann komplexe Websites wie eurobuch.de verstehen
- ✅ Extrahiert strukturierte Buchdaten aus HTML
- ✅ Robust gegen Website-Änderungen
- ✅ Kann mehrere Quellen parallel crawlen
- ✅ Kosten-effizient mit Gemini 2.0 Flash

**Anwendungsfall:**
```python
# Beispiel: Eurobuch.de nach Buch-ISBN suchen
isbn = "9783423282388"
url = f"https://www.eurobuch.de/buch/isbn/{isbn}.html"

# Gemini crawlt die Seite und extrahiert:
result = {
    "price_range": {"min": 4.99, "max": 12.50},
    "availability": "27 Angebote",
    "condition_stats": {"neu": 5, "gebraucht": 22},
    "average_price": 7.85,
    "publishers_found": ["dtv", "Goldmann"],
    "editions_found": ["Taschenbuch", "Gebunden"]
}
```

**Mögliche Quellen:**
- 📚 eurobuch.de - Preis-Aggregator
- 📚 zvab.com - Antiquarische Bücher
- 📚 booklooker.de - Gebrauchtbuchmarkt
- 📚 abebooks.de - Internationale Angebote
- 📚 amazon.de - Marktpreise und Rezensionen

**Implementierungs-Komplexität:** 🟢 Niedrig (2-3 Tage)

---

### 2. Grounding with Google Search ⭐ EMPFOHLEN

**Was es ist:**
Gemini-Feature das automatisch Google Search nutzt um aktuelle Informationen zu finden.

**Vorteile für unsere Pipeline:**
- ✅ **Bereits in Gemini integriert** - keine separate API
- ✅ Findet aktuelle Marktpreise
- ✅ Entdeckt neue Editionen
- ✅ Verifiziert Buchdaten
- ✅ Sehr kosten-effizient

**Anwendungsfall:**
```python
from google import genai
from google.genai import types

client = genai.Client()

# Nutze Google Search als Tool
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents=f'Finde aktuelle Marktpreise für ISBN {isbn} in Deutschland',
    config=types.GenerateContentConfig(
        tools=[{"google_search": {}}]  # ← Aktiviert Google Search
    )
)

# Gemini nutzt automatisch Google Search und gibt strukturierte Antwort
```

**Was es findet:**
- Aktuelle Verkaufspreise
- Verfügbarkeit bei Online-Händlern
- Editionen und Veröffentlichungsdaten
- Rezensionen und Bewertungen
- Vergleichbare Bücher

**Implementierungs-Komplexität:** 🟢 Sehr niedrig (1 Tag)

---

### 3. Vertex AI Search ⚠️ NICHT EMPFOHLEN

**Was es ist:**
Enterprise Search Engine für strukturierte und unstrukturierte Daten.

**Warum NICHT geeignet:**
- ❌ **Benötigt eigenen Datenindex** - müssen wir selbst befüllen
- ❌ **Teuer** - $1.50 pro 1000 Queries
- ❌ **Overhead** - komplex zu setup und maintain
- ❌ **Overkill** - für unseren Use Case zu mächtig

**Bessere Alternative:** Google Search Grounding (siehe oben)

---

### 4. Vertex AI Agent Builder (Reasoning Engine) 🤔 OPTIONAL

**Was es ist:**
Low-code Platform für Multi-Agent Workflows mit reasoning capabilities.

**Vorteile:**
- ✅ Kann komplexe Multi-Step Recherchen durchführen
- ✅ Orchestriert mehrere Datenquellen
- ✅ Reasoning über Ergebnisse

**Nachteile:**
- ⚠️ Noch in Preview
- ⚠️ Zusätzliche Komplexität
- ⚠️ Wir haben bereits eine funktionierende Agent-Architektur

**Empfehlung:** Später evaluieren, wenn grundlegende Integration funktioniert

---

## 🏗️ Implementierungsstrategie

### Phase 1: Gemini Web Scraper (Priorität: HOCH)

**Ziel:** Erweitere Data Fusion Engine mit intelligentem Web Scraping

**Architektur:**
```
Existing Data Sources:
├── Google Books API
├── OpenLibrary API
└── AI Extraction (Gemini Vision)

NEW Data Sources:
├── Gemini Web Scraper
│   ├── eurobuch.de (Preise + Verfügbarkeit)
│   ├── ZVAB (Antiquarische Bücher)
│   └── booklooker.de (Gebrauchtmarkt)
└── Google Search Grounding
    ├── Aktuelle Marktpreise
    ├── Neue Editionen
    └── Verifikation
```

**Implementation Plan:**

#### Step 1: Web Scraper Client erstellen
```python
# shared/apis/web_scraper.py

from google import genai
from google.genai import types
import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class GeminiWebScraper:
    """
    Intelligenter Web Scraper der Gemini nutzt um Websites zu analysieren.
    """
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.client = genai.Client()
        self.model = "gemini-2.0-flash-exp"
    
    async def scrape_eurobuch(self, isbn: str) -> Dict[str, Any]:
        """
        Crawlt eurobuch.de nach Preis- und Verfügbarkeitsinformationen.
        
        Args:
            isbn: ISBN des Buches
            
        Returns:
            Dict mit Preisinformationen, Verfügbarkeit, Zustand
        """
        url = f"https://www.eurobuch.de/buch/isbn/{isbn}.html"
        
        prompt = f"""
        Analysiere diese Webseite und extrahiere Buchinformationen:
        URL: {url}
        
        Extrahiere folgende Daten als JSON:
        {{
          "price_range": {{"min": float, "max": float}},
          "average_price": float,
          "availability": "X Angebote",
          "condition_stats": {{"neu": int, "gebraucht": int, "sehr_gut": int}},
          "sellers": int,
          "editions_found": ["Taschenbuch", "Gebunden", ...],
          "confidence": 0.0-1.0
        }}
        
        Wenn die Seite nicht existiert oder keine Daten hat, gib confidence=0.0 zurück.
        """
        
        try:
            # Nutze Gemini mit URL Grounding
            response = await self.client.models.generate_content_async(
                model=self.model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Niedrig für faktische Extraktion
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            logger.info(f"Eurobuch scrape successful for ISBN {isbn}")
            return result
            
        except Exception as e:
            logger.error(f"Eurobuch scrape failed for {isbn}: {e}")
            return {"confidence": 0.0, "error": str(e)}
    
    async def scrape_zvab(self, title: str, author: str) -> Dict[str, Any]:
        """Crawlt ZVAB nach antiquarischen Angeboten."""
        # Ähnliche Implementation wie eurobuch
        pass
    
    async def scrape_multiple_sources(
        self, 
        isbn: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Crawlt mehrere Quellen parallel.
        
        Returns:
            Liste von Ergebnissen von verschiedenen Quellen
        """
        tasks = []
        
        if isbn:
            tasks.append(self.scrape_eurobuch(isbn))
            # tasks.append(self.scrape_zvab_by_isbn(isbn))
        
        if title and author:
            # tasks.append(self.scrape_zvab(title, author))
            # tasks.append(self.scrape_booklooker(title, author))
            pass
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter erfolgreiche Ergebnisse
        return [r for r in results if isinstance(r, dict) and r.get("confidence", 0) > 0.3]
```

#### Step 2: Google Search Grounding hinzufügen
```python
# shared/apis/search_grounding.py

from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class GoogleSearchGrounding:
    """
    Nutzt Google Search Grounding für aktuelle Marktdaten.
    """
    
    def __init__(self):
        self.client = genai.Client()
        self.model = "gemini-2.0-flash-exp"
    
    async def search_market_prices(
        self, 
        isbn: str,
        title: str,
        author: str
    ) -> Dict[str, Any]:
        """
        Nutzt Google Search um aktuelle Marktpreise zu finden.
        
        Returns:
            Dict mit Preisinformationen und Quellen
        """
        prompt = f"""
        Finde aktuelle Marktpreise für dieses Buch:
        - ISBN: {isbn}
        - Titel: {title}
        - Autor: {author}
        
        Suche nach:
        1. Verkaufspreisen bei deutschen Online-Buchhändlern
        2. Gebrauchtpreisen
        3. Verfügbarkeit
        
        Gib die Ergebnisse als JSON zurück:
        {{
          "new_price_range": {{"min": float, "max": float}},
          "used_price_range": {{"min": float, "max": float}},
          "availability": "string",
          "sources": ["source1", "source2", ...],
          "confidence": 0.0-1.0
        }}
        """
        
        try:
            response = await self.client.models.generate_content_async(
                model=self.model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],  # ← Google Search aktiviert
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            
            # Log welche Seiten verwendet wurden
            if response.candidates[0].grounding_metadata:
                search_queries = response.candidates[0].grounding_metadata.web_search_queries
                logger.info(f"Search queries used: {search_queries}")
            
            return result
            
        except Exception as e:
            logger.error(f"Search grounding failed: {e}")
            return {"confidence": 0.0, "error": str(e)}
    
    async def verify_book_data(
        self,
        existing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verifiziert vorhandene Buchdaten mit Google Search.
        
        Nützlich um:
        - Falsche Editionen zu erkennen
        - Veraltete Informationen zu updaten
        - Neue Editionen zu entdecken
        """
        prompt = f"""
        Verifiziere diese Buchdaten:
        {json.dumps(existing_data, indent=2)}
        
        Prüfe ob:
        1. Titel und Autor korrekt sind
        2. Das Erscheinungsjahr stimmt
        3. Die Edition korrekt ist
        4. Es neuere Editionen gibt
        
        Gib zurück:
        {{
          "verified": boolean,
          "corrections": {{"field": "corrected_value", ...}},
          "new_editions_found": [...],
          "confidence": 0.0-1.0
        }}
        """
        
        # Implementation ähnlich zu search_market_prices
        pass
```

#### Step 3: Data Fusion Engine erweitern
```python
# In shared/apis/data_fusion.py

class DataFusionEngine:
    def __init__(self):
        # Existing clients
        self.openlibrary_client = OpenLibraryClient()
        self.google_books_client = GoogleBooksClient(...)
        
        # NEW: Web Scraping + Search
        self.web_scraper = GeminiWebScraper(project_id=GCP_PROJECT)
        self.search_grounding = GoogleSearchGrounding()
    
    async def enhanced_book_research_v2(
        self,
        base_data: Dict[str, Any],
        image_urls: List[str]
    ) -> Dict[str, Any]:
        """
        V2 mit Web Scraping und Search Grounding.
        """
        # Existing research (Google Books + OpenLibrary + AI)
        existing_result = await self.enhanced_book_research(base_data, image_urls)
        
        # NEW: Web Scraping
        isbn = base_data.get('isbn')
        title = base_data.get('title')
        author = base_data.get('author')
        
        scraping_results = []
        if isbn:
            scraping_results = await self.web_scraper.scrape_multiple_sources(
                isbn=isbn, 
                title=title, 
                author=author
            )
        
        # NEW: Google Search Grounding
        search_result = await self.search_grounding.search_market_prices(
            isbn=isbn,
            title=title,
            author=author
        )
        
        # Fuse all data sources
        fused_data = self._fuse_all_sources(
            existing_result,
            scraping_results,
            search_result
        )
        
        # Enhanced metadata
        fused_data["_metadata"]["sources_used"].extend([
            "eurobuch_scraping",
            "google_search_grounding"
        ])
        
        # Recalculate confidence with new sources
        fused_data["confidence_score"] = self._calculate_enhanced_confidence(
            fused_data
        )
        
        return fused_data
    
    def _calculate_enhanced_confidence(self, data: Dict[str, Any]) -> float:
        """
        Erweiterte Confidence-Berechnung mit Web Scraping.
        
        Source Weights:
        - Google Books: 1.0
        - OpenLibrary: 0.9
        - Web Scraping (eurobuch): 0.85
        - Google Search Grounding: 0.8
        - AI Extraction: 0.4
        """
        weights = {
            "google_books": 1.0,
            "openlibrary": 0.9,
            "eurobuch_scraping": 0.85,
            "google_search_grounding": 0.8,
            "ai_extraction": 0.4
        }
        
        sources_used = data["_metadata"].get("sources_used", [])
        
        if not sources_used:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights.get(s, 0.5) for s in sources_used)
        confidence = total_weight / len(sources_used)
        
        return min(confidence, 1.0)
```

---

## 💰 Kosten-Analyse

### Gemini Web Scraping

**Kosten pro Buch:**
- Gemini 2.0 Flash: $0.000075 per 1K input tokens
- Eurobuch-Seite: ~5K tokens
- ZVAB-Seite: ~5K tokens
- Parsing: ~2K output tokens

**Gesamt: ~$0.001 pro Buch** (sehr günstig!)

### Google Search Grounding

**Kosten:**
- Inkludiert in Gemini API Kosten
- Keine zusätzlichen Charges für Search
- ~1K output tokens: $0.0003

**Gesamt: ~$0.0003 pro Search** (extrem günstig!)

### Vergleich zu Vertex AI Search

**Vertex AI Search:**
- $1.50 per 1000 queries
- **= $0.0015 pro Query** (5x teurer als unsere Lösung)
- Plus Setup und Maintenance Overhead

**Empfehlung:** Gemini Web Scraping + Search Grounding ist **deutlich günstiger und flexibler**

---

## 📊 Erwartete Verbesserungen

### Datenqualität

**Vor Vertex AI Integration:**
- Confidence bei ISBN-Match: ~0.85
- Confidence ohne ISBN: ~0.6
- Editions-Genauigkeit: ~70%

**Nach Vertex AI Integration:**
- Confidence bei ISBN-Match: ~0.92 (+7%)
- Confidence ohne ISBN: ~0.75 (+15%)
- Editions-Genauigkeit: ~85% (+15%)

### Neue Datenfelder

**Preisinformationen:**
```json
{
  "market_data": {
    "new_price_range": {"min": 12.99, "max": 19.99},
    "used_price_range": {"min": 4.99, "max": 9.99},
    "average_market_price": 8.50,
    "availability": "gut verfügbar",
    "sellers_count": 27
  }
}
```

**Editions-Details:**
```json
{
  "edition_analysis": {
    "detected_edition": "dtv Taschenbuch, 5. Auflage",
    "other_editions_available": [
      "Gebundene Ausgabe (Erstausgabe)",
      "E-Book",
      "Hörbuch"
    ],
    "publication_history": [
      {"year": 2015, "edition": "Erstausgabe"},
      {"year": 2020, "edition": "Taschenbuch"}
    ]
  }
}
```

---

## 🚀 Implementation Timeline

### Week 1: Foundation
- [ ] GeminiWebScraper Client erstellen
- [ ] GoogleSearchGrounding Client erstellen
- [ ] Unit Tests schreiben
- [ ] Basic Integration in Data Fusion Engine

### Week 2: Integration
- [ ] Eurobuch.de Scraping implementieren
- [ ] Google Search Grounding integrieren
- [ ] Enhanced Confidence Scoring
- [ ] End-to-End Testing

### Week 3: Expansion
- [ ] ZVAB Scraping hinzufügen
- [ ] Booklooker.de optional
- [ ] Performance Optimierung
- [ ] Documentation

### Week 4: Production
- [ ] Load Testing
- [ ] Error Handling Refinement
- [ ] Deploy to Alpha
- [ ] Monitor und Optimize

---

## ⚠️ Considerations & Risks

### Technisch

1. **Rate Limiting**
   - Eurobuch.de könnte Rate Limits haben
   - **Lösung:** Caching, delays zwischen Requests

2. **Website Changes**
   - Websites können ihre Struktur ändern
   - **Lösung:** Gemini ist robust gegen kleine Änderungen

3. **Kosten**
   - Mehr API Calls = höhere Kosten
   - **Lösung:** Caching, nur bei Bedarf scrapen

### Legal

1. **Web Scraping Legalität**
   - Muss robots.txt respektieren
   - Keine persönlichen Daten sammeln
   - **Lösung:** Nur öffentliche Produktdaten

2. **Terms of Service**
   - Websites könnten Scraping verbieten
   - **Lösung:** Prüfen, ggf. APIs nutzen

---

## 🎯 Empfehlung

**Start mit:**
1. ✅ **Gemini Web Scraper** für eurobuch.de
2. ✅ **Google Search Grounding** für Verifikation

**Später evaluieren:**
- ZVAB Scraping
- Booklooker.de
- Amazon Product API (wenn verfügbar)

**NICHT nutzen:**
- ❌ Vertex AI Search (Overkill und teuer)
- ❌ Vertex AI Agent Builder (noch zu komplex)

---

## 📚 Nächste Schritte

1. **Review dieses Dokuments** mit dem Team
2. **Entscheidung:** Welche Quellen zuerst implementieren?
3. **Prototype erstellen:** GeminiWebScraper + Eurobuch
4. **Testing:** Mit echten ISBNs
5. **Integration:** In Data Fusion Engine
6. **Deploy:** Alpha-Launch

---

**Dokument erstellt:** 2025-11-04  
**Version:** 1.0  
**Status:** Proposal - Awaiting Approval  
**Nächster Review:** Nach Prototype Implementation