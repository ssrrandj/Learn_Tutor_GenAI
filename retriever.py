import os
from llama_index.core import StorageContext, load_index_from_storage
from reranker import rerank_chunks

def detect_topic(question, topics):
    if not topics:
        return None
    q = question.lower()
    for t in topics:
        if t.lower() in q:
            return t
    return None

def retrieve_chunks(index, question):
    """
    Contract: 
    1. index: The loaded LlamaIndex 'Brain' from app.py
    2. question: The user's query or the chapter title
    """
    print("\n--- 🔍 RETRIEVAL DEBUG ---")
    
    if index is None:
        print("❌ ERROR: Retriever received 'None' for index. The book might not be loaded.")
        return []

    try:
        # Step 1: Broad Retrieval
        # We grab 10 candidates so the Reranker has a good selection to choose from
        retriever = index.as_retriever(similarity_top_k=10)
        nodes = retriever.retrieve(question)
        
        # Step 2: Extract content
        # Note: In newer LlamaIndex versions, it's often node.node.text or node.text
        raw_chunks = [node.node.get_content() for node in nodes]
        print(f"📊 Initial candidates found: {len(raw_chunks)}")

        if not raw_chunks:
            print("⚠️ No matching content found in the book.")
            return []

        # Step 3: Reranking (The Intelligence Layer)
        # This uses your reranker.py to pick the most relevant 5 chunks
        print("🧠 Reranking for precision...")
        ranked_results = rerank_chunks(question, raw_chunks, top_k=5)
        
        # Extract just the text from the (text, score) tuples
        final_chunks = [text for text, score in ranked_results]
        
        print(f"✅ Final chunks selected: {len(final_chunks)}")
        return final_chunks

    except Exception as e:
        print(f"❌ Retrieval Failed: {e}")
        return []