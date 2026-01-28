
try:
    import google.generativeai as genai
    print("SUCCESS: google.generativeai imported successfully")
except ImportError as e:
    print(f"ERROR: {e}")
