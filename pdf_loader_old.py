import os
from llama_parse import LlamaParse

def load_document(file_path, is_academic=True):
    if is_academic:
        # 1. Force the key here to ensure it's not 'None'
        parser = LlamaParse(
            api_key="llx-RjALa7BlskzcaZnIbNDptGDY3Beg09IkRl0hhodLrWkUUlNL", # PASTE YOUR KEY DIRECTLY FOR A SEC TO TEST
            result_type="markdown",
            num_workers=4,
            verbose=True,
            language="en"
        )
        
        # 2. Get the data
        documents = parser.load_data(file_path)
        
        # 3. VERIFY: LlamaParse returns a list of Document objects. 
        # We need to ensure the text is actually there.
        if documents:
            print(f"✅ LlamaParse Success: Extracted {len(documents)} pages.")
            return documents
        else:
            print("❌ LlamaParse returned empty list.")
            return []
    else:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        return loader.load()