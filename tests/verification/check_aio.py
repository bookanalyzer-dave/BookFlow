
import os
import sys

# Set a dummy API key if not present, just in case Client validation requires it
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "dummy_key"

try:
    from google import genai
    print(f"Successfully imported google.genai")
except ImportError:
    print("Failed to import google.genai")
    sys.exit(1)

try:
    client = genai.Client()
    print(f"Successfully created client instance: {client}")
    
    if hasattr(client, 'aio'):
        print("\nSUCCESS: 'aio' attribute EXISTS on client instance.")
        print(f"Type of client.aio: {type(client.aio)}")
        print(f"client.aio: {client.aio}")
    else:
        print("\nFAILURE: 'aio' attribute DOES NOT EXIST on client instance.")
        
    print("\nClient attributes:")
    print(dir(client))
    
except Exception as e:
    print(f"An error occurred: {e}")
