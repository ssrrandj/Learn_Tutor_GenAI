try:
    from google import genai
    from google.genai import types
except ImportError:
    import google.genai as genai

from pdf2image import convert_from_path # Essential import for PDF conversion
import sys
import os
import time

# 1. FORCE THE PATH (Maintained from your working version)
site_pkg_path = r"C:\GenAI\Learn_APP_F\ENV_learn1\Lib\site-packages" 
if site_pkg_path not in sys.path:
    sys.path.append(site_pkg_path)

def run_vision_test(pdf_path=None, index_page=None):
    """
    Maintains the accurate logic of the original script 
    but allows app.py to pass the current PDF and page number.
    """
    
    # --- CONFIGURATION ---
    GEMINI_API_KEY = ""
    POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin" 
    
    # Fallback to hardcoded values only if app.py doesn't provide them
    final_pdf_path = pdf_path if pdf_path else r"C:\Users\rajan\OneDrive\Desktop\Telangana-board-class-10-Physical-Science-Textbook-English-Medium.pdf"
    final_page_num = index_page if index_page else 11

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"--- Starting Final Vision Test on: {os.path.basename(final_pdf_path)} ---")
    
    # STEP 1: PDF to Image
    try:
        print(f"Converting PDF page {final_page_num} to image...")
        images = convert_from_path(
            final_pdf_path, 
            first_page=final_page_num, last_page=final_page_num,
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

    # STEP 2: The Model Loop (Exactly as you had it)
    test_models = [
        "gemini-2.5-flash", 
        "gemini-3-flash", 
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    
    for model_name in test_models:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=["List every chapter title from this image exactly. No page numbers.", img]
            )
            print(f"\n SUCCESS WITH {model_name}!")
            return response.text.strip() 
            
        except Exception as e:
            if "404" in str(e):
                print(f"  {model_name} not found, trying next...")
                time.sleep(2)
                continue
            elif "429" in str(e):
                print("  Rate limit hit. Please wait.")
                return ""
            else:
                print(f"  Error: {e}")
                return ""

if __name__ == "__main__":
    # This allows you to still run it as a standalone script for testing
    result = run_vision_test()
    print("-" * 30)
    print(result)
    print("-" * 30)