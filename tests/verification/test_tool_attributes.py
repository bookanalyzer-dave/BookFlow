
import vertexai
from vertexai.generative_models import Tool

print("Available attributes in Tool:")
for attr in dir(Tool):
    if not attr.startswith("_"):
        print(f"- {attr}")
        
try:
    print("\nAttempting to import grounding from vertexai.preview.generative_models...")
    from vertexai.preview.generative_models import grounding
    print("Success importing from preview.")
    print("Available attributes in preview grounding:")
    for attr in dir(grounding):
        if not attr.startswith("_"):
            print(f"- {attr}")

except ImportError:
    print("Failed importing from preview.")
