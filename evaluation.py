from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")


def semantic_score(answer, chunks):

    if not chunks:
        return 0

    answer_emb = model.encode(answer, convert_to_tensor=True)
    chunk_emb = model.encode(" ".join(chunks), convert_to_tensor=True)

    score = util.cos_sim(answer_emb, chunk_emb)
    return float(score)


def retrieval_score(question, chunks):

    if not chunks:
        return 0

    q_emb = model.encode(question, convert_to_tensor=True)
    c_emb = model.encode(" ".join(chunks), convert_to_tensor=True)

    score = util.cos_sim(q_emb, c_emb)
    return float(score)
