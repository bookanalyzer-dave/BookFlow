"""
Price Grounding Client
Nutzt Vertex AI Gemini 2.5 Pro mit Search Grounding für ISBN-basierte Preisrecherche.
"""

import os
import json
import logging
import asyncio
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
# Patch aiohttp for google-genai compatibility issue
import aiohttp
if not hasattr(aiohttp, 'ClientConnectorDNSError'):
    try:
        aiohttp.ClientConnectorDNSError = aiohttp.ClientConnectorError
    except:
        pass
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

@dataclass
class PriceGroundingConfig:
    model: str = "gemini-2.5-pro"
    temperature: float = 0.1
    max_output_tokens: int = 4096
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    retry_exponential_base: float = 2.0

DEFAULT_CONFIG = PriceGroundingConfig()

@dataclass
class PriceData:
    """Strukturierte Preisdaten von einem Verkäufer."""
    seller: str
    price_eur: float
    condition: str
    url: Optional[str] = None
    availability: Optional[str] = None
    platform: str = "unknown"

@dataclass
class MarketQueryResult:
    """Gesamtergebnis der Marktrecherche inkl. KI-Bewertung."""
    offers: List[PriceData]
    confidence_score: float
    reasoning: str

class PriceGroundingClient:
    """Client für Gemini-basierte Preissuche mit Search Grounding."""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1", config: PriceGroundingConfig = DEFAULT_CONFIG):
        self.project_id = project_id or os.getenv("GCP_PROJECT")
        self.location = location
        self.config = config
        
        # Initialisierung analog zu ingestion-agent: Versuche API Key, sonst Vertex AI
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
             self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )

    async def search_market_prices(
        self, 
        isbn: str, 
        title: Optional[str] = None,
        author: Optional[str] = None,
        publisher: Optional[str] = None,
        year: Optional[int] = None,
        edition: Optional[str] = None
    ) -> MarketQueryResult:
        """
        Sucht Marktpreise über mehrere Quellen (Eurobuch, ZVAB, etc.) via Gemini Grounding.
        Nutzt zusätzliche Metadaten (Autor, Verlag, etc.) für eine präzisere Zuordnung der Ausgabe.
        """
        
        prompt = self._build_combined_search_prompt(
            isbn=isbn, 
            title=title, 
            author=author, 
            publisher=publisher, 
            year=year, 
            edition=edition
        )
        
        generate_content_config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            automatic_function_calling={'disable': False, 'maximum_remote_calls': 10},
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
        )

        for attempt in range(self.config.retry_attempts + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retrying search for ISBN {isbn} (Attempt {attempt}/{self.config.retry_attempts})")
                
                # Use aio for async call
                response = await self.client.aio.models.generate_content(
                    model=self.config.model,
                    contents=prompt,
                    config=generate_content_config
                )
                
                return self._process_response(response, isbn)

            except Exception as e:
                is_retryable = '429' in str(e) or 'quota' in str(e).lower() or 'resource exhausted' in str(e).lower()
                if not is_retryable or attempt >= self.config.retry_attempts:
                    logger.error(f"❌ Grounding search failed for ISBN {isbn} after {attempt} retries: {e}", exc_info=True)
                    # Return empty result on failure to avoid crashing the flow
                    return MarketQueryResult(
                        offers=[],
                        confidence_score=0.0,
                        reasoning=f"Search failed: {str(e)}"
                    )
                
                delay = self.config.retry_delay_seconds * (self.config.retry_exponential_base ** attempt)
                await asyncio.sleep(delay)

        return MarketQueryResult(offers=[], confidence_score=0.0, reasoning="Max retries reached")

    def _process_response(self, response: Any, isbn: str) -> MarketQueryResult:
        """Parses the Gemini response using robust patterns."""
        result_text, finish_reason = self._get_response_text(response)
        
        if not result_text.strip():
            logger.warning(f"⚠️ Empty response from Gemini Grounding for ISBN {isbn}. Finish reason: {finish_reason}")
            return MarketQueryResult(offers=[], confidence_score=0.0, reasoning=f"Empty response from AI (Reason: {finish_reason})")

        try:
            result_json = self._parse_json_response(result_text)
            
            all_prices = []
            offers = result_json.get("offers", [])
            confidence_score = float(result_json.get("overall_confidence_score", 0.0))
            reasoning = result_json.get("reasoning", "")

            for offer in offers:
                try:
                    all_prices.append(PriceData(
                        seller=offer.get("seller", "Unknown"),
                        price_eur=float(offer.get("price_eur", 0)),
                        condition=offer.get("condition", "Unknown"),
                        url=offer.get("url"),
                        availability=offer.get("availability"),
                        platform=offer.get("platform", "unknown")
                    ))
                except Exception as val_e:
                    logger.error(f"Validation error for offer in ISBN {isbn}: {val_e}")
            
            logger.info(f"✅ Gemini Grounding found {len(all_prices)} prices for ISBN {isbn} with confidence {confidence_score}")
            return MarketQueryResult(
                offers=all_prices,
                confidence_score=confidence_score,
                reasoning=reasoning
            )

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse response for ISBN {isbn}. Error: {e}")
            # Try to debug by logging truncated text
            logger.error(f"❌ Problematic text (first 200 chars): {result_text[:200]}")
            return MarketQueryResult(offers=[], confidence_score=0.0, reasoning=f"JSON Parse Error: {str(e)}")
        except Exception as e:
             logger.error(f"❌ Unexpected error processing response for ISBN {isbn}: {e}", exc_info=True)
             return MarketQueryResult(offers=[], confidence_score=0.0, reasoning=f"Processing Error: {str(e)}")

    def _get_response_text(self, response: Any) -> Tuple[str, Optional[str]]:
        """Safely extracts text from the response and returns it along with the finish reason."""
        finish_reason = None
        try:
            if hasattr(response, 'candidates') and response.candidates:
                cand = response.candidates[0]
                if hasattr(cand, 'finish_reason'):
                    finish_reason = str(cand.finish_reason)
                    logger.info(f"Candidate finish reason: {finish_reason}")
            
            return response.text, finish_reason
        except Exception as e:
            logger.warning(f"Could not get response.text directly: {e}")
            
            if hasattr(response, 'candidates') and response.candidates:
                cand = response.candidates[0]
                # finish_reason already extracted above if possible, but let's be safe
                if not finish_reason and hasattr(cand, 'finish_reason'):
                    finish_reason = str(cand.finish_reason)
                    logger.info(f"Candidate finish reason (fallback): {finish_reason}")
                
                if hasattr(cand.content, 'parts') and cand.content.parts:
                    for part in cand.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text, finish_reason
            else:
                logger.warning(f"No candidates in response: {response}")
        
        return "", finish_reason

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Robustly parses JSON from text, handling Markdown blocks and raw JSON."""
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            clean_text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
            clean_text = re.sub(r"^```\s*", "", clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r"```$", "", clean_text, flags=re.MULTILINE).strip()
            return json.loads(clean_text)

    def _build_combined_search_prompt(
        self, 
        isbn: str, 
        title: Optional[str],
        author: Optional[str] = None,
        publisher: Optional[str] = None,
        year: Optional[int] = None,
        edition: Optional[str] = None
    ) -> str:
        """Erstellt einen optimierten Prompt für die Suche."""
        context_parts = [f"ISBN: {isbn}"]
        if title: context_parts.append(f"Titel: {title}")
        if author: context_parts.append(f"Autor: {author}")
        if publisher: context_parts.append(f"Verlag: {publisher}")
        if year: context_parts.append(f"Erscheinungsjahr: {year}")
        if edition: context_parts.append(f"Auflage/Ausgabe: {edition}")
            
        context = ", ".join(context_parts)
            
        return f"""
        Recherchiere aktuelle Verkaufspreise für exakt diese Buchausgabe auf deutschen Online-Marktplätzen:
        {context}
        
        Nutze die oben genannten Metadaten (Autor, Verlag, Jahr, Auflage), um sicherzustellen, dass nur Preise für diese spezifische Ausgabe zurückgegeben werden. 
        Dies ist besonders wichtig bei verschiedenen Editionen oder Einbänden des gleichen Titels.

        Suche gezielt auf:
        1. Eurobuch.com (Meta-Suche über 50+ Quellen) - URL: https://www.eurobuch.com/buch/isbn/{{isbn}}
        2. ZVAB.com (Zentrales Verzeichnis Antiquarischer Bücher) - URL: https://www.zvab.com/servlet/SearchResults?isbn={{isbn}}
        3. Booklooker.de
        
        Fokus: Gebrauchte Bücher in verschiedenen Zuständen.
        
        Extrahiere für jedes gefundene Angebot:
        - seller: Name des Händlers/Antiquariats
        - price_eur: Preis in Euro (nur die Zahl)
        - condition: Zustand (z.B. "Wie neu", "Sehr gut", "Gut", "Akzeptabel")
        - url: Direktlink zum Angebot
        - availability: Verfügbarkeit
        - platform: Die Plattform (eurobuch, zvab, booklooker)
        
        Bewerte die Qualität der gefundenen Daten:
        - overall_confidence_score: Ein Wert zwischen 0.0 und 1.0. 
          * Berücksichtige die Anzahl der gefundenen Quellen (mehr Quellen = höherer Score).
          * Berücksichtige die Übereinstimmung der Metadaten (Titel, Autor, Verlag, Jahr).
          * Berücksichtige die Preisvarianz (hohe Varianz bei identischer Ausgabe = niedrigerer Score).
        - reasoning: Eine kurze Begründung deiner Einschätzung (auf Deutsch).

        WICHTIG:
        - Erfinde keine Daten! Gib nur reale Angebote zurück.
        - Vergleiche die gefundenen Ergebnisse mit dem Verlag ({publisher if publisher else 'unbekannt'}) und Jahr ({year if year else 'unbekannt'}), um Fehlzuordnungen zu vermeiden.
        - Wenn keine Angebote für diese spezifische Ausgabe gefunden werden, gib ein leeres Array zurück, einen Score von 0.0 und eine entsprechende Begründung.
        - Preise OHNE Versandkosten.

        Gib das Ergebnis als reines JSON zurück. Verwende dazu folgenden Code-Block:
        ```json
        {{
          "offers": [
            {{
              "seller": "Name",
              "price_eur": 12.50,
              "condition": "Gut",
              "url": "http://...",
              "availability": "Lieferbar",
              "platform": "eurobuch"
            }}
          ],
          "overall_confidence_score": 0.9,
          "reasoning": "Begründung..."
        }}
        ```
        """
