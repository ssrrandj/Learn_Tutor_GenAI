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

def retrieve_chunks(index, question, chat_history=None):
    """
    Contract: 
    1. index: The loaded LlamaIndex 'Brain'
    2. question: The user's query
    3. chat_history: List of last 4 messages (Sliding Window)
    """
    print("\n--- 🔍 RETRIEVAL DEBUG ---")
    
    if index is None:
        print("❌ ERROR: Retriever received 'None' for index.")
        return []

    # --- NEW: QUERY TRANSFORMATION ---
    search_query = question
    if chat_history and len(chat_history) > 0:
        print("🔄 Context detected. Rephrasing query for better search...")
        # We use a simple prompt to turn follow-ups into standalone searches
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
        
        rephrase_prompt = f"""
        Given the following chat history, rephrase the user's latest question 
        to be a standalone search query that includes all necessary context.
        
        History: {history_str}
        Latest Question: {question}
        Standalone Search Query:"""
        
        # We use the existing index as a quick tool to rephrase
        from llama_index.core import Settings
        query_engine = index.as_query_engine(llm=Settings.llm) 
        search_query = str(query_engine.query(rephrase_prompt)).strip()
        print(f"🔎 New Search Query: {search_query}")

    try:
        # Step 1: Broad Retrieval (Using the REPHRASED query)
        retriever = index.as_retriever(similarity_top_k=10)
        nodes = retriever.retrieve(search_query) 
        
        # Step 2: Extract content
        raw_chunks = [node.node.get_content() for node in nodes]
        print(f"📊 Initial candidates found: {len(raw_chunks)}")

        if not raw_chunks:
            return []

        # Step 3: Reranking (Still using the original question for relevance)
        print("🧠 Reranking for precision...")
        ranked_results = rerank_chunks(search_query, raw_chunks, top_k=5)
        
        final_chunks = [text for text, score in ranked_results]
        print(f"✅ Final chunks selected: {len(final_chunks)}")
        return final_chunks

    except Exception as e:
        print(f"❌ Retrieval Failed: {e}")
        return []