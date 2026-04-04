import ollama
import streamlit as st
import os
import re
from langchain_community.vectorstores import Chroma
from embedding import get_embeddings
from groq import Groq
from answer import get_model, build_context

client = Groq(api_key="Groq_key")
# removed Groq key from above to be able to push to github

@st.cache_data
def extract_topics(chunks):

    models_check = client.models.list().data
    print("Available Models:")
    for m in models_check:
        print(m.id)

    print("You are here topics.py")
    #def extract_topics(book_name,summary):

    #context = "\n".join(chunks[:5]) old working

    context = build_context(chunks, max_chunks=800)

    print("type of context:", type(context))

    print("context lenght;", len(context))

    model_name = get_model()

    print("model name selected for topics.py:", model_name)

    prompt = f"""
You are analyzing textbook content.

Task:
Extract topics EXACTLY as they appear in the text, and classify what each one represents.

Rules:
- Topic must be copied EXACTLY from the content (no modification)
- Do NOT replace with abstract concepts
- Add a short classification label (e.g., Poem, Story, Concept, Exercise)
- Classification should be based only on the content (no guessing)

Context:
{context}

Output format:
- Exact Topic (Type)
"""

    

    #prompt = f"""
#Extract important textbook topics.


#Context:
#{context}

#Only return topics.
#"""
        #return response.choice[0].message.content
    print("printing prompt to chekc what it is feeding:topic.py", prompt)
    models = client.models.list().data

    #model_name = None

    if model_name is None:
        raise Exception("No model found")

    

    for m in models:
        if any(x in m.id.lower() for x in ["mistral","llama","gemma"]):
            model_name = m.id
            break

        print("selected model:", model_name)


    response = client.chat.completions.create(
        model =model_name,
        messages = [{"role": "user",
                    "content": prompt}
                    ],
                    temperature = 0
    )

    raw  = response.choices[0].message.content

    print("Raw LLM output: \n", raw)

    topics = [t.strip("- ").strip()  for t in raw.split("\n") if t.strip()]

    return topics[:10]
    

    #return response.choices[0].message.content


    # Commented below code which was used for local llm, instead added code above to call Groq llm through API

#     print("Extracting topics")

#     print(f"loading summary from extract topic {book_name}")

#     prompt = f"""
#     You are an API that extracts topics.

# From the following book summary, return only a list of topics.

# STRICT RULES:
# - Output ONLY bullet points
# - Each line MUST start with "-"
# - maximum 5 topics
# - Each topic MUST be under 6 words
# - NO explanations
# - No paragraphs
# - No Numberering
# - No headings
# - No extra text

# Example Output:

# - Topic One
# - Topic Two
# - Topic Three

# Return only bullet points.

# Summary:
# {summary}

# """
#     reponse = ollama.chat(
#         model = "phi3",
#         messages=[{"role": "user",
#                    "content": prompt}]
#     )
#     result = reponse["message"]["content"]
#     clean = "\n".join([
#         line for line in result.split("\n")
#         if line.strip().startswith("-")
#     ])

#     return clean

def load_topics(book,BASE):

    print("Loading topics")

    path = "topics.txt"

    #folder = os.path.join(BASE, path)

    folder = BASE + f'/{path}'

    print("topics file name",folder)

    if os.path.exists(folder):
        with open(folder, "r", encoding="utf-8") as f:
        
            print(f"loading summary from {folder}")
            return f.read().split("\n")
        
    return None


def load_summary(book,BASE):

    print("loading summary")

    path = "summary.txt"

    #summary_path = os.path.join(BASE, path)

    summary_path = BASE + f'/{path}'

    print("topics file name",summary_path)

    #summary_path = f"books/{book}/summary.txt"

    if not os.path.exists(summary_path):
        return None

    with open(summary_path, "r", encoding="utf-8") as f:
        
        print(f"loading summary from {summary_path}")
        return f.read()