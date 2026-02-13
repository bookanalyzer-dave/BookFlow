import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

for m in genai.list_models():
    print(f"Model: {m.name}")
    print(f"  Supported methods: {m.supported_generation_methods}\n")