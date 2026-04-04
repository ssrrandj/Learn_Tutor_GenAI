from langchain_community.retrievers import BM25Retriever
from reranker import rerank_chunks

def detect_topic(question, topics):
    q = question.lower()
    for t in topics:
        if t.lower() in q:
            return t
    return None

def retrieve_chunks(question, vector_db, topics):

    detected_topic = detect_topic(question, topics)

    queries = [
        question,
        f"Explain {question}",
        f"Detailed explanation of {question}"
    ]

    all_chunks = []

    for q in queries:
        if detected_topic:
            results = vector_db.similarity_search(q, k=10, filter={"topic": detected_topic})
        else:
            results = vector_db.similarity_search(q, k=10)

        all_chunks.extend([doc.page_content for doc in results])

        print("vector results",len(all_chunks))
    
    print("Question:", question)

    combined = list(dict.fromkeys(all_chunks))

    print("after cleaning:", len(combined))

    if not combined:
        print("no chunks after cleaning")
        return[]

    bm25 = BM25Retriever.from_texts(combined)
    bm25.k = 5

    keyword_chunks = [doc.page_content for doc in bm25.invoke(question)]

    combined = list(dict.fromkeys(combined + keyword_chunks))

    ranked = rerank_chunks(question, combined, top_k=10)

    print("reranked:",len(ranked))

    #return [c for c, s in ranked if s > 0.2][:8]
    #return [c for c, s in ranked[:2]]

    final_chunks = [c for c, _ in ranked[:3]]

    print("Final chunks", len(final_chunks))

    if not final_chunks:
        print("Using fall back")
        return combined[:3]
    
    return final_chunks