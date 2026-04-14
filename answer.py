from groq import Groq
import os

# Logic: Use an environment variable or a direct key. 
# In app.py, we should ideally pass this or set it globally.
client = Groq(api_key="")

def get_model():
    """
    Contract: Returns the latest supported Llama model on Groq.
    Updated: Replaced decommissioned llama3-70b-8192 with llama-3.3-70b-versatile.
    """
    # Llama 3.3 70B is the direct current successor for high-quality tutoring.
    return "llama-3.3-70b-versatile" 

def build_context(chunks, max_chars=4000):
    """
    Contract: Merges retrieved textbook chunks into a single string.
    """
    context = ""
    for c in chunks:
        if len(context) + len(c) > max_chars:
            break
        context += f"[Textbook Segment]:\n{c}\n\n---\n\n"
    return context

def generate_answer(chunks, question):
    """
    Contract: Generates a factual answer based ONLY on textbook context.
    """
    if not chunks:
        return "I'm sorry, I couldn't find any specific information about that in the uploaded textbook."

    context = build_context(chunks)
    
    # Logic: High-instruction prompt to ensure 'Silo' integrity
    system_prompt = (
        "You are an expert academic tutor. Use the provided textbook context to answer the student's question. "
        "If the answer is not in the context, say you don't know based on the book. "
        "Keep the tone encouraging and clear."
    )
    
    user_prompt = f"Textbook Context:\n{context}\n\nStudent Question: {question}"

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2 # Lower temperature = more factual/less creative
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def generate_quiz(chunks, topic):
    """
    Contract: Generates a quiz from the specific chapter context.
    """
    context = build_context(chunks[:3]) # Use a bit more context for better questions
    
    prompt = f"""
    Based on the following textbook context, create 3-5 multiple-choice questions for the topic: {topic}.
    
    Context:
    {context}
    
    Format:
    Q1: [Question]
    A) [Option]
    B) [Option]
    C) [Option]
    D) [Option]
    Correct Answer: [Letter]
    """
    
    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating quiz: {str(e)}"