
try:
    import vertexai
    print(f"Vertex AI version: {vertexai.__version__}")
except AttributeError:
    print("Vertex AI version unknown (no __version__ attribute)")
except ImportError:
    print("Failed to import vertexai")

try:
    from google.cloud import aiplatform
    print(f"AI Platform version: {aiplatform.__version__}")
except ImportError:
    print("Failed to import google.cloud.aiplatform")

print("\nInspecting vertexai contents:")
for attr in dir(vertexai):
    if not attr.startswith("_"):
        print(f"- {attr}")
