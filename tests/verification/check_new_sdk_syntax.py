
try:
    from google import genai
    from google.genai import types
    print("Successfully imported google.genai")
    
    # Try to create a tool with google search
    try:
        # Check if GoogleSearch exists in types
        if hasattr(types, 'GoogleSearch'):
            print("types.GoogleSearch exists")
            gs = types.GoogleSearch()
            tool = types.Tool(google_search=gs)
            print("Successfully created Tool with google_search")
        else:
            print("types.GoogleSearch does NOT exist")
            
    except Exception as e:
        print(f"Error creating Tool: {e}")

except ImportError:
    print("Could not import google.genai")
