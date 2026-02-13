
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

    # Teste explizit gemini-2.0-flash-exp (wird oft als 2.x missverstanden)
    # Und die stabilen 1.5er
    models_to_check = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    print("Checking model availability and Search Grounding...")
    for model_name in models_to_check:
        print(f"\n--- Model: {model_name} ---")
        try:
            # Versuch mit Search Grounding
            response = client.models.generate_content(
                model=model_name,
                contents="Was kostet das Buch mit der ISBN 9783453524620 aktuell?",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    max_output_tokens=200
                )
            )
            print(f"✅ {model_name} supports Search Grounding!")
            if response.candidates and response.candidates[0].content.parts:
                print(f"Response: {response.text[:100]}...")
            
            # Check grounding metadata
            if response.candidates[0].grounding_metadata:
                print("Grounding metadata found.")
                
        except Exception as e:
            msg = str(e)
            if "403" in msg:
                 print(f"🚫 {model_name} PERMISSION DENIED (403) - Check Service Account Permissions")
            elif "404" in msg:
                 print(f"❌ {model_name} NOT FOUND (404)")
            else:
                 print(f"❓ {model_name} error: {msg[:100]}")

except Exception as e:
    print(f"Failed to test: {e}")
