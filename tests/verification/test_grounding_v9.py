
import os
import traceback
from google import genai
from google.genai import types

# Projekt-ID aus Ingestion Agent
project_id = "project-52b2fab8-15a1-4b66-9f3"
location = "us-central1"

print(f"Initializing GenAI Client for project {project_id} in {location}...")

try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

    # Wir testen EXAKT die ID, die der User wünscht
    model_name = "gemini-2.5-pro"
    print(f"\n--- Testing Model: {model_name} ---")
    
    try:
        # Einfacher Testaufruf
        response = client.models.generate_content(
            model=model_name,
            contents="Hallo",
            config=types.GenerateContentConfig(max_output_tokens=10)
        )
        print(f"✅ {model_name} is REACHABLE!")
        print(f"Response: {response.text}")
        
        # Test mit Search Grounding
        print(f"\nTesting {model_name} with Search Grounding...")
        response = client.models.generate_content(
            model=model_name,
            contents="Was kostet das Buch mit der ISBN 9783453524620 aktuell?",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=100
            )
        )
        print(f"✅ {model_name} supports Search Grounding!")
        
    except Exception as e:
        msg = str(e)
        if "403" in msg:
             print(f"🚫 {model_name} PERMISSION DENIED (403)")
        elif "404" in msg:
             print(f"❌ {model_name} NOT FOUND (404)")
        else:
             print(f"❓ {model_name} error: {msg}")

except Exception as e:
    print(f"Failed to test: {e}")
