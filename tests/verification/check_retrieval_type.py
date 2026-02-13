
try:
    from google import genai
    from google.genai import types
    print("Successfully imported google.genai")
    
    if hasattr(types, 'GoogleSearchRetrieval'):
        print("types.GoogleSearchRetrieval exists")
    else:
        print("types.GoogleSearchRetrieval does NOT exist")
        
    if hasattr(types, 'GoogleSearch'):
        print("types.GoogleSearch exists")
        
except ImportError:
    print("Could not import google.genai")
