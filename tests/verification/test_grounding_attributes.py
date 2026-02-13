
import os
import traceback
from google import genai
from google.genai import types

# Projekt-ID aus Ingestion Agent
project_id = "project-52b2fab8-15a1-4b66-9f3"
location = "europe-west1"

print(f"Initializing GenAI Client for project {project_id} in {location}...")

try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )

    models_to_check = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    
    print("Checking model availability in europe-west1...")
    for model_name in models_to_check:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="hi",
                config=types.GenerateContentConfig(max_output_tokens=1)
            )
            print(f"✅ {model_name} is available in {location}")
        except Exception as e:
            print(f"❌ {model_name} in {location} error: {str(e)[:100]}")

except Exception as e:
    print(f"Failed to test: {e}")
