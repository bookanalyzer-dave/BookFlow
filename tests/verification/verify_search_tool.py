
import os
import asyncio
from google import genai
from google.genai import types

# Use dummy project if not set, hoping for ADC or just checking syntax
PROJECT_ID = os.environ.get("GCP_PROJECT", "project-52b2fab8-15a1-4b66-9f3")
LOCATION = "us-central1"

async def test_search_config(tool_config_name):
    print(f"\n--- Testing {tool_config_name} ---")
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        
        if tool_config_name == "google_search_retrieval":
            tool = types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())
        elif tool_config_name == "google_search":
            tool = types.Tool(google_search=types.GoogleSearch())
        else:
            print("Unknown config")
            return

        config = types.GenerateContentConfig(
            tools=[tool],
            response_mime_type="application/json"
        )
        
        # We don't necessarily need to call the API to check if the OBJECT creation works, 
        # but the user said it "fails", which could be runtime.
        # Let's try a dry run or just print the config object to see if it serialized correctly.
        print(f"Tool created successfully: {tool}")
        print(f"Config created successfully.")
        
        # Optional: Try a real call if we dare (might fail due to quota/auth)
        # response = await client.aio.models.generate_content(
        #     model="gemini-2.5-pro",
        #     contents="What is the price of iPhone 15?",
        #     config=config
        # )
        # print("API Call successful")
        
    except Exception as e:
        print(f"FAILED with {tool_config_name}: {e}")

async def main():
    await test_search_config("google_search_retrieval")
    await test_search_config("google_search")

if __name__ == "__main__":
    asyncio.run(main())
