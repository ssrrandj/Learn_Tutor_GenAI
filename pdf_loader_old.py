import os
from llama_parse import LlamaParse
from dotenv import load_dotenv

load_dotenv()

def load_document(file_path, is_academic=True):
    if is_academic:
        # 1. Force the key here to ensure it's not 'None'
        parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"), # PASTE YOUR KEY DIRECTLY FOR A SEC TO TEST
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
    
import re

def filter_topic_content(text):
    # This regex looks for 'UNIT' followed by Roman Numerals and a colon
    # Pattern: Case-insensitive 'UNIT', space, Roman numeral/digit, colon, then the title
    # We replaced .*? with [^\n]+ to ensure it grabs everything until the line ends
    pattern = r"(?i)(UNIT\s+[IVXLC\d]+:\s*[^\n]+)"
    
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None # Or return the original if no match

import re


def extract_units_with_content(raw_text):
    """
    Finds each UNIT and captures the text block immediately following it.
    """
    # 1. (?i) -> Case insensitive
    # 2. UNIT\s+[IVXLC\d]+: -> Matches 'UNIT I:'
    # 3. \s* -> Cleans up any space/newlines
    # 4. (.*?) -> Non-greedily captures the content
    # 5. (?=UNIT|$) -> Lookahead: Stops when it hits the next UNIT or end of file
    pattern = r"(?i)(UNIT\s+[IVXLC\d]+:)\s*(.*?)(?=UNIT|$)"
    
    # re.DOTALL is critical here; it allows the '.' to match newline characters
    matches = re.findall(pattern, raw_text, re.DOTALL)
    
    results = []
    for header, content in matches:
        # Clean up the paragraph text (remove extra newlines/spaces)
        clean_content = " ".join(content.split())
        results.append(f"{header} {clean_content}")
        
    return results