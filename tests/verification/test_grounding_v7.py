
import os
import traceback
from google import genai
from google.genai import types

# Projekt-ID aus der gcloud-Konfiguration
project_id = "project-52b2fab8-15a1-4b66-9f3"
# Ingestion Agent nutzt us-central1
location = "us-central1"

print(f"Initializing GenAI Client for project {project_id} in {location}...")

try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

    # Wir testen die "neuesten" IDs, falls "gemini-2.5-pro" ein Platzhalter für 2.0 ist
    models_to_check = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    print("Checking model availability and Search Grounding...")
    for model_name in models_to_check:
        print(f"\n--- Model: {model_name} ---")
        try:
            # Minimaler Aufruf OHNE Tools um generelle Erreichbarkeit zu prüfen
            response = client.models.generate_content(
                model=model_name,
                contents="hi",
                config=types.GenerateContentConfig(max_output_tokens=1)
            )
            print(f"✅ {model_name} is reachable (Standard)")
            
            # Jetzt mit Search Grounding
            print(f"Testing {model_name} with Search Grounding...")
            response = client.models.generate_content(
                model=model_name,
                contents="Was kostet das Buch mit der ISBN 9783453524620 aktuell?",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    max_output_tokens=100
                )
            )
            print(f"✅ {model_name} supports Search Grounding!")
            
            break # Nimm das erste verfügbare Modell
                
        except Exception as e:
            msg = str(e)
            if "404" in msg:
                 print(f"❌ {model_name} NOT FOUND (404)")
            elif "403" in msg:
                 print(f"🚫 {model_name} PERMISSION DENIED (403)")
            else:
                 print(f"❓ {model_name} error: {msg[:100]}")

except Exception as e:
    print(f"Failed to test: {e}")
