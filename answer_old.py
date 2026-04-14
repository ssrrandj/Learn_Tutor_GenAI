from groq import Groq

client = Groq(api_key="YOUR_GROQ_KEY")

def get_model():
    models = client.models.list().data
    for m in models:
        if "llama-3" in m.id.lower():
            return m.id
    return "llama3-8b-8192"

def build_context(chunks, max_chars=3500):
    context = ""
    for c in chunks:
        if len(context) + len(c) > max_chars:
            break
        context += c + "\n\n---\n\n"
    return context

def generate_answer(chunks, question):
    if not chunks:
        return "I couldn't find relevant content in the textbook."
    context = build_context(chunks)
    prompt = f"Teacher Mode: Answer using this context:\n{context}\n\nQuestion: {question}"
    response = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def generate_quiz(chunks, question):
    # Take first 2 chunks for context to keep quiz focused
    context = "\n".join(chunks[:2])
    prompt = f"""
    Create 5 MCQs based on this context:
    {context}
    
    Topic: {question}
    Format:
    1. Question?
    A) ... B) ... C) ... D) ...
    Answer: ...
    """
    response = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content