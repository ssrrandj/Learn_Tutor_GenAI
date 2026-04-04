import streamlit as st
import os
import re
import time

from auth import login, signup
from pdf_loader import load_pdf
from chunk import dynamic_chunking
from vector_db import create_vector_store
from retriever import retrieve_chunks
from answer import generate_answer, generate_quiz
from voice import speak_answer
from embedding import get_embeddings
from langchain_community.vectorstores import Chroma
from groq import Groq
from topics import extract_topics

# ---------------- SESSION INIT ----------------
if "mode" not in st.session_state:
    st.session_state.mode = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- CSS ----------------
def load_css():
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------------- GROQ ----------------
client = Groq(api_key="YOUR_API_KEY")

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.clear()
    st.rerun()

# ---------------- TITLE ----------------
st.markdown('<div class="title">Smart Learning App</div>', unsafe_allow_html=True)
st.title("📘 AI Tutor")                                                                      
# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            with st.spinner("Logging in..."):
                if login(u, p):
                    st.session_state.user = u
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid login")

    with tab2:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")

        if st.button("Signup"):
            with st.spinner("Signing up..."):
                if signup(u, p):
                    st.success("User created")
                else:
                    st.error("User exists")

    st.stop()

# ---------------- PATH ----------------
BASE = f"storage/books/{st.session_state.user}"
os.makedirs(BASE, exist_ok=True)

@st.cache_resource
def load_db(path):
    return Chroma(persist_directory=path, embedding_function=get_embeddings())

def file_clean(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

# ---------------- LLM TOPIC FALLBACK ----------------
def extract_topics_with_llm(chunks):
    sample = "\n".join(chunks[:10])

    prompt = f"""
Extract 5 main topics from this textbook.

Rules:
- Only short phrases
- One topic per line

Content:
{sample}
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    topics = response.choices[0].message.content.split("\n")
    return [t.strip("- ").strip() for t in topics if t.strip()]

# ---------------- UPLOAD ----------------
file = st.file_uploader("Upload PDF", type=["pdf"])

if file:
    name = file_clean(file.name.replace(".pdf", ""))
    folder = os.path.join(BASE, name)
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, file.name)

    with open(path, "wb") as f:
        f.write(file.read())

    if st.button("Process"):
        with st.spinner("Processing book..."):
            docs = load_pdf(path)
            chunks = dynamic_chunking(docs)

            if not chunks:
                st.error("No text extracted")
                st.stop()

            topics = extract_topics(chunks)

            if not topics:
                topics = extract_topics_with_llm(chunks)

            if not topics:
                topics = ["General Concepts"]

            with open(f"{folder}/topics.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(topics))

            create_vector_store(chunks, os.path.join(folder, "vector_db"), topics)

        st.success("Book processed!")

# ---------------- SELECT BOOK ----------------
books = os.listdir(BASE)
book = st.selectbox("Select Book", books)

if not book:
    st.stop()

folder = os.path.join(BASE, book)
db_path = os.path.join(folder, "vector_db")

if not os.path.exists(db_path):
    st.warning("Process book first")
    st.stop()

db = load_db(db_path)

# ---------------- LOAD TOPICS ----------------
topics_path = os.path.join(folder, "topics.txt")

with open(topics_path, "r", encoding="utf-8") as f:
    topics = [t.strip() for t in f.read().split("\n") if t.strip()]

# ---------------- DISPLAY FUNCTION ----------------
def display_ans(answer):
    
    col1, col2 = st.columns([1, 5])

    with col1:
        if "avatar" in st.session_state:
            st.image(st.session_state.avatar, width=100)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)

    with col2:
        st.markdown(f'<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown("### Answer")
        st.markdown(f'<div class="answer">{answer}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    

# ---------------- TOPICS ----------------
st.subheader("📖 Topics")

for i, t in enumerate(topics):
    if st.button(t, key=f"{t}_{i}"):
        st.session_state.topic = t

# ---------------- TOPIC CLICK ----------------
if "topic" in st.session_state:
    st.session_state.pop("current_quiz", None)

    def clean_topic(text):
        text = text.split(".", 1)[-1] if "." in text else text
        text = text.split("(", 1)[0]
        return text.strip()

    q = f"Explain {clean_topic(st.session_state.topic)}"

    chunks = retrieve_chunks(q, db, topics)
    answer = generate_answer(chunks, q)

    st.session_state.output = answer
    st.session_state.mode = "topic"

# ---------------- ASK ----------------
q = st.text_input("Ask a question")

if st.button("Ask"):
    # clear old quiz First
    st.session_state.pop("current_quiz", None)

    if not q:
        st.warning("Enter a question")
        st.stop()

    chunks = retrieve_chunks(q, db, topics)

    with st.spinner("Thinking..."):
        time.sleep(1)
        answer = generate_answer(chunks, q)

    st.session_state.output = answer
    st.session_state.mode = "ask"
    st.session_state.current_chunks = chunks

# ---------------- FINAL DISPLAY ----------------
if "output" in st.session_state and st.session_state.output:

    display_ans(st.session_state.output)

    st.audio(speak_answer(st.session_state.output))

    if st.session_state.get("mode") == "ask":
        with st.expander("📄 Retrieved Content"):
            for c in st.session_state.get("current_chunks", []):
                st.write(c)

# -------------------Quiz ---------- Clock

# ---------------- QUIZ ----------------
if "output" in st.session_state and st.session_state.output:

     with st.expander("Quiz click to expand"):
         
        if st.button("🧠 Generate Quiz"):
        

            chunks = st.session_state.get("current_chunks", [])

            if not chunks:
                st.warning("Ask a question first to generate quiz")
            else:
                with st.spinner("Generating quiz..."):
                    quiz = generate_quiz(
                        chunks,
                        st.session_state.get("current_question", "")
                    )

            # ✅ store quiz
                st.session_state.current_quiz = quiz

    # ✅ always display quiz if exists
if "current_quiz" in st.session_state:

        st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown("### 🧪 Quiz")
        st.markdown(f'<div class="answer">{st.session_state.current_quiz}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 👤 Profile")

    avatar_file = st.file_uploader(
        "Upload Avatar",
        type=["png", "jpg", "jpeg"]
    )

    if avatar_file:
        st.session_state.avatar = avatar_file

    if "avatar" in st.session_state:
        st.image(st.session_state.avatar, width=120)

# ---------------- LOGOUT ----------------
with st.sidebar:
    if st.button("Logout"):
        logout()