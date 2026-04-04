from groq import Groq

client = Groq(api_key="api_key")

def get_model():
     models = client.models.list().data
     print("model from answer.py",models)

     for m in models:
         if "llama-3" in m.id.lower() or "llama-4" in m.id.lower():
             return m.id
     return None
    

     #return next((m.id for m in models if "llama" in m.id.lower())
      #           , None)
models_check = client.models.list().data
print("Available Models:")
for m in models_check:
     print(m.id)


    

    #return "llama-3.3-8b-instant"
   

     """for m in models:
        if "llama" in m.id.lower():
            return m.id
        
        return "llama3-8b-8192"""
    

def build_context(chunks, max_chunks=800):
    
    context = ""

    for c in chunks:
         #if len(context)  + len(c) > max_chunks:
             #break
         chunk_part = c[:200]

         if len(context) + len(chunk_part) > max_chunks:
             break
         context += chunk_part + "\n\n"

    return context



def generate_answer(chunks, question):

    if not chunks:
        return "I can not find this in the book."
    context = build_context(chunks)

    print("Final context length:", len(context) )

    #context = "\n\n".join(chunks[:4])
    #trimmed_chunks = [c[:500] for c in chunks[:4]]
    #context = "\n\n".join(trimmed_chunks)
#    Use ONLY the book content.
#Combine all relevant parts.
#Show key content
#2. Explain simply


    prompt = f"""
You are a helpfull teacher.

Use the book content below to answer.

If exact answer is not found, try to explain based on available content

Content:
{context}

Question:
{question}

Answer:

1. Key points
2. Simple explanation 
"""
    print("printing prompt to chekc what it is feeding:topic.py", prompt)
    response = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    print("chunks:", len(chunks))

    #print("Sample chunk:", chunks[0] if chunks else "No chunks")

    return response.choices[0].message.content


def generate_quiz(chunks, question):

    context = "\n".join(chunks[:2])

    print("Quiz context input length:", len(context))

    prompt = f"""
Create ONLY or Maximum 5 MCQs based STRICTLY on the question below.

Question:
{question}

Context:
{context}

Rules:
- Questions MUST be ONLY about the question topic
- DO NOT include other topics
- DO NOT ask about other rhymes
- Keep questions SHORT
- DO NOT ask to "write full rhyme"
- Focus on meaning, facts, or small details

Output format:
1. Question?
A) ...
B) ...
C) ...
D) ...
Answer: ...
"""
    print("promtp input to llm:", prompt)
    response = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )



    return response.choices[0].message.content