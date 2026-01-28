
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

with open("available_models.txt", "w") as f:
    if not api_key:
        f.write("No API key found in .env\n")
    else:
        genai.configure(api_key=api_key)
        f.write("Listing available models...\n")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
