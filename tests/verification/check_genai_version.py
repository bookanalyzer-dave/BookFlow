
import sys
import importlib.util

print(f"Python version: {sys.version}")

try:
    import google.generativeai as genai
    print(f"google.generativeai version: {genai.__version__}")
    print(f"google.generativeai file: {genai.__file__}")
    
    from google.generativeai.types import Tool
    print("Tool class found in google.generativeai.types")
    # check Tool signature if possible
    import inspect
    print(f"Tool init signature: {inspect.signature(Tool.__init__)}")
except ImportError as e:
    print(f"google.generativeai import failed: {e}")

try:
    from google import genai
    print(f"google.genai (new SDK) found")
    # print(f"google.genai version: {genai.__version__}") # might not have version at top level
except ImportError as e:
    print(f"google.genai import failed: {e}")

import pkg_resources
for dist in pkg_resources.working_set:
    if "google" in dist.project_name:
        print(f"{dist.project_name}=={dist.version}")
