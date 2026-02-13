
import os
import traceback
from google import genai
from google.genai import types

# Verwende die Projekt-ID aus der gcloud-Konfiguration
project_id = os.environ.get("GCP_PROJECT", "project-52b2fab8-15a1-4b66-9f3")
# Teste in us-central1 mit API Key
api_key = os.environ.get("GOOGLE_API_KEY")

print(f"Initializing GenAI Client for project {project_id}...")

try:
    if api_key:
        print("Using API Key for authentication (Developer API)...")
        client = genai.Client(api_key=api_key)
        
        models_to_check = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        
        print("Checking model availability via API KEY...")
        for model_name in models_to_check:
            try:
                # Minimal call
                response = client.models.generate_content(
                    model=model_name,
                    contents="hi",
                    config=types.GenerateContentConfig(max_output_tokens=1)
                )
                print(f"✅ {model_name} is available")
            except Exception as e:
                msg = str(e)
                print(f"❌ {model_name} error: {msg[:100]}")
    else:
        print("GOOGLE_API_KEY not found in environment.")

except Exception as e:
    print(f"Failed to test models: {e}")
