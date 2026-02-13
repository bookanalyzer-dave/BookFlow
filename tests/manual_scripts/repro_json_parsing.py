
import json
import re
import logging
import sys

# Encoding fix for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Simuliere Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_json_old(result_text):
    """Die alte, fehleranfällige Logik aus core.py (vereinfacht)"""
    print(f"\n--- Testing OLD Logic with input length {len(result_text)} ---")
    try:
        result_json = None
        # Strategie 1: Finde erstes '{' und letztes '}'
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = result_text[start_idx:end_idx+1]
            try:
                result_json = json.loads(json_str)
                print("OLD: JSON erfolgreich via Substring-Extraction extrahiert")
                return result_json
            except json.JSONDecodeError as e:
                print(f"OLD: Substring-Extraction fehlgeschlagen: {e}")
        
        # Strategie 2: Markdown Cleanup (Fallback)
        if result_json is None:
            clean_text = re.sub(r"^```json\s*", "", result_text, flags=re.MULTILINE)
            clean_text = re.sub(r"^```\s*", "", clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r"```$", "", clean_text, flags=re.MULTILINE).strip()
            result_json = json.loads(clean_text)
            print("OLD: Markdown-bereinigter Text als JSON geladen")
            return result_json

    except json.JSONDecodeError as e:
        print(f"OLD: JSON DECODE ERROR: {e}")
        return None

def extract_json_new(text):
    """
    Versucht, JSON aus einem String zu extrahieren.
    Strategie:
    1. Suche nach Code-Blöcken ```json ... ``` oder ``` ... ```.
       Nimm den *letzten* Block, da Modelle oft erst erklären und dann das Ergebnis liefern.
    2. Wenn keine Code-Blöcke, suche nach dem äußersten JSON-Objekt {...}.
       Wenn mehrere gefunden werden, nimm das letzte gültige.
    """
    print(f"\n--- Testing NEW Logic with input length {len(text)} ---")
    
    # 1. Versuche, Markdown Code-Blöcke zu finden
    # Wir suchen nach ```json ... ``` oder einfach ``` ... ```
    # flags=re.DOTALL damit . auch Newlines matcht
    code_block_pattern = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
    matches = code_block_pattern.findall(text)
    
    if matches:
        print(f"Found {len(matches)} code blocks.")
        # Wir probieren die Matches von hinten nach vorne
        for json_str in reversed(matches):
            try:
                parsed = json.loads(json_str)
                print("NEW: Valid JSON found in markdown code block (reverse order)")
                return parsed
            except json.JSONDecodeError:
                continue
    
    # 2. Fallback: Suche nach JSON-Objekten im Rohtext mit Regex
    # Wir suchen alle '{' und versuchen von dort aus zu parsen.
    
    decoder = json.JSONDecoder()
    idx = 0
    candidates = []
    
    while idx < len(text):
        # Finde nächstes '{'
        start_idx = text.find('{', idx)
        if start_idx == -1:
            break
            
        try:
            obj, end_idx = decoder.raw_decode(text, start_idx)
            candidates.append(obj)
            idx = end_idx # Weiter nach dem Ende des gefundenen Objekts suchen
        except json.JSONDecodeError:
            # Kein valides JSON an dieser Stelle, weiter suchen
            idx = start_idx + 1
            
    if candidates:
        print(f"Found {len(candidates)} JSON candidates in raw text.")
        # Wir nehmen das letzte Objekt, da dies wahrscheinlich das Ergebnis ist
        print("NEW: Selected last valid JSON candidate")
        return candidates[-1]

    print("NEW: No valid JSON found anywhere.")
    return None


# --- TEST CASES ---

# Case 1: The problematic "Chatty" response from the user report
case_1 = """Okay, ich werde die Buchbilder analysieren... Hier ist das JSON-Format, das ich verwenden werde:
```json
{
  "book_data": {
    "title": "Example Title"
  }
}
```
Das ist nur ein Beispiel.

Hier ist das tatsächliche Ergebnis der Analyse:
```json
{
  "book_data": {
    "title": "Der Herr der Ringe",
    "authors": ["J.R.R. Tolkien"],
    "isbn": "978-3-608-93828-9",
    "condition": "GOOD"
  },
  "confidence": 0.98
}
```
Ich hoffe das hilft!"""

# Case 2: Simple valid JSON
case_2 = """{
  "book_data": { "title": "Simple Book" }
}"""

# Case 3: Dirty raw text without code blocks (multiple objects)
case_3 = """Ich habe das Buch gefunden.
Beispiel: {"test": 123}
Aber hier sind die Daten:
{"book_data": {"title": "Real Book"}, "confidence": 1.0}
Danke."""

# Case 4: Broken JSON in middle
case_4 = """
Hier ist ein JSON:
```json
{ "title": "Broken", 
```
Ups, abgebrochen. Hier nochmal:
```json
{ "title": "Fixed" }
```
"""

# Case 5: Nested JSON (Testing raw_decode capability)
case_5 = """
Some text
{
  "outer": {
     "inner": "value"
  }
}
End text
"""

print("==================================================")
print("TEST CASE 1: Chatty Response (Two Blocks)")
res_old_1 = extract_json_old(case_1)
res_new_1 = extract_json_new(case_1)
print(f"Result Old: {res_old_1.get('book_data', {}).get('title') if res_old_1 else 'None'}")
print(f"Result New: {res_new_1.get('book_data', {}).get('title') if res_new_1 else 'None'}")

print("\n==================================================")
print("TEST CASE 2: Simple JSON")
extract_json_new(case_2)

print("\n==================================================")
print("TEST CASE 3: Raw Text Multiple Objects")
res_old_3 = extract_json_old(case_3) 
res_new_3 = extract_json_new(case_3)
print(f"Result Old: {res_old_3}") 
print(f"Result New: {res_new_3}")

print("\n==================================================")
print("TEST CASE 4: Broken Block First")
extract_json_new(case_4)

print("\n==================================================")
print("TEST CASE 5: Nested JSON")
extract_json_new(case_5)
