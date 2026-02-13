import json
import re

def extract_json(result_text):
    print(f"Original Text Length: {len(result_text)}")
    print(f"Snippet: {result_text[:200]}...")

    result_json = None
    
    # Strategie 1: Suche nach Markdown Code-Blöcken
    code_block_pattern = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
    matches = code_block_pattern.findall(result_text)
    
    if matches:
        print(f"Found {len(matches)} code blocks")
        for json_str in reversed(matches):
            try:
                result_json = json.loads(json_str)
                print("Valid JSON found in code block")
                return result_json
            except json.JSONDecodeError:
                continue

    # Strategie 2: Raw Text Scanning
    if result_json is None:
        print("Scanning raw text...")
        decoder = json.JSONDecoder()
        idx = 0
        candidates = []
        
        while idx < len(result_text):
            # Finde nächstes '{'
            start_idx = result_text.find('{', idx)
            if start_idx == -1:
                break
                
            try:
                # Versuch, ein JSON-Objekt zu parsen
                obj, end_idx = decoder.raw_decode(result_text, start_idx)
                candidates.append(obj)
                idx = end_idx # Weiter nach dem gefundenen Objekt
            except json.JSONDecodeError:
                idx = start_idx + 1 # Wenn Fehler, versuche nächstes Zeichen
        
        if candidates:
            print(f"Found {len(candidates)} JSON candidates")
            result_json = candidates[-1]
            return result_json
            
    return None

# Testfall aus den Logs rekonstruiert (vereinfacht)
log_text = """Okay, ich werde die Buchbilder analysieren und die Metadaten extrahieren, um das Buch zu identifizieren. Ich werde Google Search verwenden, um die Informationen zu verifizieren und fehlende Details zu ergänzen.

*   **Titel:** Copper and Copper Alloys: A Series of Lectures on Copper and Copper Alloys Presented to Members of the ASM During the Twenty-ninth National Metal Congress and Exposition, Chicago, Octob
Basierend auf den Bildern und den Suchergebnissen, hier sind die Metadaten des Buches:

```json
{
  "title": "Copper and Copper Alloys",
  "author": "Owen W. Ellis",
  "publisher": "American Society for Metals",
  "year": 1948
}
```
"""

# Ein Fall wo kein Code Block ist, aber JSON im Text (was der aktuelle Fehler zu sein scheint, da er "No valid code blocks found" loggt)
# Aber Moment! Die Logs zeigen Markdown Listen, aber KEIN JSON im Output Snippet in den Logs.
# "Basierend auf den Bildern und den Suchergebnissen, hier sind die Metadaten des Buches:" steht am Ende des Log Snippets.
# Es sieht so aus, als ob das Modell gar kein JSON generiert hat, sondern nur Markdown.

text_no_json = """Okay, ich werde die Buchbilder analysieren...
* **Titel:** Copper...
* **Autor:** Owen...
"""

print("--- Test 1: Mit Code Block ---")
print(extract_json(log_text))

print("\n--- Test 2: Ohne JSON (Nur Text) ---")
print(extract_json(text_no_json))
