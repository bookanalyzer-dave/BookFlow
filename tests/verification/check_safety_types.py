
try:
    from google import genai
    from google.genai import types
    print("google-genai imported successfully")
    
    print("\nHarmBlockThreshold members:")
    for member in types.HarmBlockThreshold:
        print(f"{member.name}: {member.value}")

    print("\nHarmCategory members:")
    for member in types.HarmCategory:
        print(f"{member.name}: {member.value}")

except ImportError:
    print("google-genai not installed")
except Exception as e:
    print(f"Error: {e}")
