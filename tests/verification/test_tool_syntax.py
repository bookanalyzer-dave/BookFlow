
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

    # Wir nutzen "gemini-1.5-flash" als Basis für den Test
    model_name = "gemini-1.5-flash"
    print(f"Testing {model_name} with different tool configurations...")
    
    # Variante A: types.Tool(google_search=types.GoogleSearch())
    print("\nVariant A: types.Tool(google_search=types.GoogleSearch())")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Was kostet das Buch mit der ISBN 9783453524620?",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=100
            )
        )
        print("✅ Variant A Success")
    except Exception as e:
        print(f"❌ Variant A Error: {str(e)[:100]}")

    # Variante B: dict-basierte Tools
    print("\nVariant B: config={'tools': [{'google_search': {}}]}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Was kostet das Buch mit der ISBN 9783453524620?",
            config={"tools": [{"google_search": {}}]}
        )
        print("✅ Variant B Success")
    except Exception as e:
        print(f"❌ Variant B Error: {str(e)[:100]}")

except Exception as e:
    print(f"Failed to test: {e}")
