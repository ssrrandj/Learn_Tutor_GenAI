import os
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from embedding import get_embeddings

def get_or_create_index(documents, user_id, clean_book_name):
    """
    Contract: Receives a sanitized 'clean_book_name' from app.py.
    Purpose: Ensures the index is buried inside the specific user silo.
    """
    # 1. Path Logic: Use the clean name directly to avoid folder duplication
    persist_dir = f"./storage/books/{user_id}/{clean_book_name}/vector_db"
    
    # 2. Initialize embeddings (Ensures Settings.embed_model is ready)
    get_embeddings()
    
    # 3. Decision Logic: Load or Create
    if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
        print(f"DEBUG: Creating new LlamaIndex at {persist_dir}")
        
        # Guard: Ensure the documents list isn't empty before indexing
        if not documents:
            print("ERROR: No documents provided to indexer.")
            return None
            
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=persist_dir)
        return index
    else:
        print(f"DEBUG: Loading existing LlamaIndex from {persist_dir}")
        
        # Logic: Reconstruct the 'Brain' from disk
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage_context)