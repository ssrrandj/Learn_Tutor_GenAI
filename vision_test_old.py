
# Initialize Client
# import sys
# import os
# import time

# # 1. FORCE THE PATH (Ensures Python sees your installed libraries)
# site_pkg_path = r"C:\\GenAI\\Learn_APP_F\\ENV_learn1\\Lib\\site-packages" 
# if site_pkg_path not in sys.path:
#     sys.path.append(site_pkg_path)

# # 2. THE IMPORTS
# try:
#     from google import genai
# except ImportError:
#     import google_genai as genai
# from pdf2image import convert_from_path

# # --- CONFIGURATION (Check these 3 lines!) ---
# GEMINI_API_KEY = "AIzaSyA9KxJJEJeRkjAUD7OJ5K2vErnBf8Q05Xk"
# PDF_PATH = r"C:\Users\rajan\OneDrive\Desktop\Telangana-board-class-10-Physical-Science-Textbook-English-Medium.pdf" 
# POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin" 
# INDEX_PAGE_NUMBER = 11

# client = genai.Client(api_key=GEMINI_API_KEY)
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fallback just in case of environment naming quirks
    import google.genai as genai
import time
import sys
import os
import time

def run_vision_test():

    

# 1. FORCE THE PATH (Ensures Python sees your installed libraries)
    site_pkg_path = r"C:\\GenAI\\Learn_APP_F\\ENV_learn1\\Lib\\site-packages" 
    if site_pkg_path not in sys.path:
        sys.path.append(site_pkg_path)


# --- CONFIGURATION (Check these 3 lines!) ---
    GEMINI_API_KEY = ""
    PDF_PATH = r"C:\Users\rajan\OneDrive\Desktop\Telangana-board-class-10-Physical-Science-Textbook-English-Medium.pdf" 
    POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin" 
    INDEX_PAGE_NUMBER = 11

    client = genai.Client(api_key=GEMINI_API_KEY)

    
    print(f"--- Starting Final Vision Test ---")
    
    # STEP 1: PDF to Image
    try:
        print("Converting PDF to image...")
        images = convert_from_path(
            PDF_PATH, 
            first_page=INDEX_PAGE_NUMBER, last_page=INDEX_PAGE_NUMBER,
            poppler_path=POPPLER_PATH,
            dpi=200
        )
        if not images:
            print("Failed to convert PDF.")
            return ""
        img = images[0]
    except Exception as e:
        print(f"Poppler Error: {e}")
        return ""

    # STEP 2: The Model Loop (Solves the 404 error)
    # We try different "names" for the same model to see what your API accepts
    test_models = ["gemini-2.5-flash",    # Current stable workhorse
    "gemini-3-flash",      # Latest high-speed frontier model
    "gemini-2.0-flash",
    "gemini-1.5-flash"]
    
    for model_name in test_models:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=["List every chapter title from this image exactly. No page numbers.", img]
            )
            print(f"\n SUCCESS WITH {model_name}!")
            print("-" * 30)
            print(response.text)
            print("-" * 30)
            return response.text.strip() # Exit once successful
            
        except Exception as e:
            if "404" in str(e):
                print(f"  {model_name} not found, trying next...")
                continue
            elif "429" in str(e):
                print("  Rate limit hit. Please wait 60 seconds and try again.")
                return ""
            else:
                print(f"  Error: {e}")
                return ""

if __name__ == "__main__":
    run_vision_test()