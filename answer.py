from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Logic: Use an environment variable or a direct key. 
# In app.py, we should ideally pass this or set it globally.
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

def generate_answer(chunks, question, chat_history=None):
    """
    Contract: Generates a factual answer based on textbook context AND conversation history.
    """
    if not chunks:
        return "I'm sorry, I couldn't find any specific information about that in the uploaded textbook."

    # Step 1: Format textbook data
    context = build_context(chunks)
    
    # Step 2: Format conversation history (The Sliding Window)
    # We convert the list of dicts into a readable string for the AI
    history_str = ""
    if chat_history:
        history_str = "\n".join([
            f"{'Student' if m['role'] == 'user' else 'Tutor'}: {m['content']}" 
            for m in chat_history
        ])

    # Step 3: Updated System Prompt
    system_prompt = (
        "You are an expert academic tutor. Use the provided textbook context to answer the student's question. "
        "Use the conversation history to maintain continuity and avoid repeating yourself. "
        "If the answer is not in the context, say you don't know based on the book. "
        "Keep the tone encouraging and clear."
    )
    
    # Step 4: Final User Prompt (Combining Context + History + Current Question)
    user_prompt = f"""
    CONVERSATION HISTORY:
    {history_str}

    TEXTBOOK CONTEXT:
    {context}

    NEW STUDENT QUESTION: {question}
    """

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2 
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