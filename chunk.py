import re
from langchain_community.vectorstores import Chroma
from embedding import get_embeddings

def load_existing_chunks(db_path):

    db = Chroma(
        persist_directory=db_path,
        embedding_function=get_embeddings()
    )

    data = db.get()

    chunks = data.get("documents", [])

    return chunks

def dynamic_chunking(docs):
    chunks = []

    for d in docs:
        parts = d.page_content.split("\n\n")
        chunks.extend(parts)

    return [c.strip() for c in chunks if len(c) > 50]


# def extract_topics(chunks):

#     from collections import Counter
#     import re

#     candidates = []

#     for c in chunks:
#         text = c.strip()

#         # Clean text
#         text = re.sub(r'\s+', ' ', text)

#         words = text.split()

#         # 🔥 Ignore very long chunks
#         if len(words) > 12:
#             continue

#         # 🔥 Ignore noise
#         if any(x in text.lower() for x in ["http", "www", ".com"]):
#             continue

#         # 🔥 Pick possible headings
#         if text.istitle() or text.isupper() or len(words) <= 6:
#             candidates.append(text)

#     # 🔥 Count frequency
#     freq = Counter(candidates)

#     # 🔥 Pick repeated ones (more likely real topics)
#     topics = [t for t, count in freq.items() if count >= 2]

#     # 🔥 Fallback if nothing found
#     if not topics:
#         topics = list(freq.keys())

#     # Remove duplicates and limit
#     topics = list(dict.fromkeys(topics))

#     return topics[:8]

# print("Total chunks:")
# print("Sample chunk:")

# def extract_topics_with_llm(chunks, client):

#     sample = "\n".join(chunks[:10])

#     prompt = f"""
# Extract 5 main topics from this textbook content.

# Rules:
# - Short phrases only
# - No sentences
# - No explanation

# Content:
# {sample}
# """

#     response = client.chat.completions.create(
#         model="llama3-8b-8192",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     topics = response.choices[0].message.content.split("\n")

#     return [t.strip("- ").strip() for t in topics if t.strip()]

def extract_topics(chunks):

    from collections import Counter
    import re

    candidates = []

    for c in chunks:
        text = c.strip()
        text = re.sub(r'\s+', ' ', text)

        words = text.split()

        if len(words) > 12:
            continue

        if any(x in text.lower() for x in ["http", "www", ".com"]):
            continue

        if text.istitle() or text.isupper() or len(words) <= 6:
            candidates.append(text)

    freq = Counter(candidates)

    topics = [t for t, count in freq.items() if count >= 2]

    if not topics:
        topics = list(freq.keys())

    topics = list(dict.fromkeys(topics))

    print("Extract_topic from gere chunks.py", len(topics))

    return topics[:8]