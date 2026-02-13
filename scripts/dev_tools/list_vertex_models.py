
import vertexai
import os
import traceback

project_id = os.environ.get("GCP_PROJECT", "project-52b2fab8-15a1-4b66-9f3")
location = "europe-west1"

print(f"Initializing Vertex AI for project {project_id} in {location}...")

try:
    vertexai.init(project=project_id, location=location)
    
    # Try importing GenerativeModel from different locations
    GenerativeModel = None
    try:
        from vertexai.generative_models import GenerativeModel
        print("Imported GenerativeModel from vertexai.generative_models")
    except ImportError:
        try:
            from vertexai.preview.generative_models import GenerativeModel
            print("Imported GenerativeModel from vertexai.preview.generative_models")
        except ImportError:
            print("Could not import GenerativeModel")
            exit(1)

    models_to_check = [
        "gemini-1.5-pro-002",
        "gemini-1.5-flash-002",
        "gemini-1.5-pro-001",
        "gemini-1.5-flash-001",
        "gemini-1.0-pro",
    ]
    
    print("Checking model availability by instantiation...")
    for model_name in models_to_check:
        try:
            model = GenerativeModel(model_name)
            # Just instantiation might not check availability in region, let's try a dummy generate if possible?
            # But without credentials it might fail differently.
            # Instantiation usually validates the name against regex but maybe not existence in backend until called.
            # However, if it throws 404 on call, that's what we want to avoid.
            print(f"✅ {model_name} instantiated successfully")
        except Exception as e:
            print(f"❌ {model_name} instantiation failed: {e}")

except Exception as e:
    print(f"Failed to init Vertex AI: {e}")
    traceback.print_exc()

