from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

def get_embeddings():
    # Matches the model in vector_db.py to ensure vector math is consistent
    model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    # Set globally so LlamaIndex uses this for all internal tasks
    Settings.embed_model = model
    return model