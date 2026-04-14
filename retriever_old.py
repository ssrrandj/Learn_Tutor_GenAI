from langchain_community.retrievers import BM25Retriever
from reranker import rerank_chunks

def detect_topic(question, topics):
    q = question.lower()
    for t in topics:
        if t.lower() in q:
            return t
    return None

import os
from llama_index.core import StorageContext, load_index_from_storage
from reranker import rerank_chunks

def retrieve_chunks(question, index, topics=None):
    """
    index: The LlamaIndex object passed from app.py
    """
    print("\n--- 🔍 RETRIEVAL DEBUG ---")
    if index is None:
        print("❌ ERROR: Index is None.")
        return []

    # Get 10 chunks to allow the reranker to pick the best ones
    retriever = index.as_retriever(similarity_top_k=10)
    
    try:
        nodes = retriever.retrieve(question)
        # Extract text content from LlamaIndex nodes
        raw_chunks = [node.node.get_content() for node in nodes]
        print(f"📊 Initial results: {len(raw_chunks)}")

        if not raw_chunks:
            return []

        # Reranking logic
        ranked_results = rerank_chunks(question, raw_chunks, top_k=5)
        final_chunks = [text for text, score in ranked_results]
        
        print(f"✅ Final chunks selected: {len(final_chunks)}")
        return final_chunks
    except Exception as e:
        print(f"❌ Retrieval Failed: {e}")
        return []