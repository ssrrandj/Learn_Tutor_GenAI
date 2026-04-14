import os
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from embedding import get_embeddings

def get_or_create_index(documents, user_id, book_name):
    # Standardized path logic
    persist_dir = f"./storage/books/{user_id}/{book_name.replace(' ', '_')}/vector_db"
    
    # Initialize embeddings
    get_embeddings()
    
    if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
        print(f"DEBUG: Creating new LlamaIndex at {persist_dir}")
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=persist_dir)
        return index
    else:
        print(f"DEBUG: Loading existing LlamaIndex from {persist_dir}")
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        return load_index_from_storage(storage_context)