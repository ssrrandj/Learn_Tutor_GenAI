from langchain_community.vectorstores import Chroma
from embedding import get_embeddings

def create_vector_store(chunks, path, topics):

    texts = []
    metas = []

    for c in chunks:
        topic = next((t for t in topics if t.lower() in c.lower()), "General")

        texts.append(c)
        metas.append({"topic": topic})

    db = Chroma.from_texts(
        texts=texts,
        embedding=get_embeddings(),
        metadatas=metas,
        persist_directory=path
    )

    db.persist()