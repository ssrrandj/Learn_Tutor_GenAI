import os
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

def load_document(file_path, is_academic=True):
    """
    Contract: 
    - If is_academic: Uses LlamaParse (Deep OCR/Markdown).
    - If not: Uses SimpleDirectoryReader (Fast/Native LlamaIndex).
    """
    print(f"\n--- 📄 LOADING DOCUMENT: {os.path.basename(file_path)} ---")
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found at {file_path}")
        return []

    if is_academic:
        print("🔍 Mode: Academic (LlamaParse OCR)")
        # 1. Initialize LlamaParse
        parser = LlamaParse(
            api_key="llx-RjALa7BlskzcaZnIbNDptGDY3Beg09IkRl0hhodLrWkUUlNL", 
            result_type="markdown",
            num_workers=4,
            verbose=True,
            language="en"
        )
        
        # 2. Extract Data
        try:
            documents = parser.load_data(file_path)
            if documents:
                print(f"✅ LlamaParse Success: Extracted {len(documents)} pages.")
                return documents
            else:
                print("⚠️ LlamaParse returned no content.")
                return []
        except Exception as e:
            print(f"❌ LlamaParse Error: {e}")
            return []

    else:
        print("⚡ Mode: Standard (Fast Load)")
        # Logic: Use LlamaIndex's native reader instead of LangChain 
        # to ensure compatibility with vector_db.py
        try:
            reader = SimpleDirectoryReader(input_files=[file_path])
            documents = reader.load_data()
            print(f"✅ Standard Load Success: {len(documents)} pages.")
            return documents
        except Exception as e:
            print(f"❌ Standard Loader Error: {e}")
            return []