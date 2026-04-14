from reranker import apply_reranking  # Your existing file
from voice import speak_text          # Your existing file

def run_tutor_query(index, query):
    # 1. Create base query engine
    query_engine = index.as_query_engine(similarity_top_k=5)
    
    # 2. Apply your existing Reranking logic
    # (Assuming apply_reranking returns a filtered response)
    response = query_engine.query(query)
    
    # 3. Trigger your Voice feature
    speak_text(str(response))
    
    return response