
import os
import traceback
from google import genai
from google.genai import types

# Projekt-ID aus der gcloud-Konfiguration
project_id = "project-52b2fab8-15a1-4b66-9f3"
# Wir versuchen es in europe-west1, da dort compute-resourcen konfiguriert sind
location = "europe-west1"

print(f"Initializing GenAI Client for project {project_id} in {location}...")

try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

    # In europe-west1 sind oft nur stabile Versionen
    models_to_check = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    print(f"Checking model availability and Search Grounding in {location}...")
    for model_name in models_to_check:
        print(f"\n--- Model: {model_name} ---")
        try:
            # Versuch mit Search Grounding
            response = client.models.generate_content(
                model=model_name,
                contents="Was kostet das Buch mit der ISBN 9783453524620 aktuell?",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    max_output_tokens=100
                )
            )
            print(f"✅ {model_name} supports Search Grounding in {location}!")
            if response.candidates and response.candidates[0].grounding_metadata:
                print("Grounding metadata found.")
            
            break
                
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
