import streamlit as st
import os
from groq import Groq
from answer import get_model, build_context

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@st.cache_data
def extract_topics(chunks):
    print("--- Starting Topic Extraction in topics.py ---")

    # FIX: Slice the list first. build_context() likely only takes one argument.
    # We take the first 20 chunks assuming the Table of Contents is at the start.
    context = build_context([c.text for c in chunks][:20]) 
    
    model_name = get_model()
    
    # IMPROVED PROMPT: Removed specific Telangana chapter names so it works for ANY book.
    prompt = f"""
STRICT TASK: Extract ONLY the main chapter titles from the provided Table of Contents text.
DO NOT use your own knowledge. 

INSTRUCTIONS:
1. Scan the text for clear chapter headings or "Contents".
2. Return a clean list of chapter titles.
3. If there are page numbers, you can include them or omit them, but keep the title clean.

CONTEXT:
{context}

OUTPUT FORMAT:
- Chapter [Number]: [Topic Name]
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0 
    )

    raw_output = response.choices[0].message.content
    print("Raw LLM Output:\n", raw_output)

    topics = []
    for line in raw_output.split("\n"):
        clean_line = line.strip("- ").strip()
        
        # Look for lines that look like a chapter title
        if clean_line and ("Chapter" in clean_line or ":" in clean_line):
            topics.append(clean_line)

        if len(topics) >= 25:
            break

    return topics