from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_chunks(question, chunks, top_k=10):

    pairs = [(question, c) for c in chunks]
    scores = model.predict(pairs)

    ranked = list(zip(chunks, scores))
    ranked.sort(key=lambda x: x[1], reverse=True)

    return ranked[:top_k]