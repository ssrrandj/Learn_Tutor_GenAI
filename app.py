import streamlit as st
import os
import re
import subprocess
from llama_index.core import StorageContext, load_index_from_storage
from groq import Groq

# --- MODULE IMPORTS ---
from auth import login, signup
from pdf_loader import load_document
from chunk import dynamic_chunking
from vector_db import get_or_create_index
from retriever import retrieve_chunks
from answer import generate_answer, generate_quiz
from voice import speak_answer
from topics import extract_topics
from vision_test import run_vision_test

# ---------------- LOGIC 1: THE SILO ARCHITECTURE ----------------
def get_isolated_path(user_id, book_name):
    base_dir = "storage/books"
    safe_user = str(user_id).strip().replace(" ", "_")
    # This removes .pdf regardless of case (PDF or pdf)
    clean_book = book_name.lower().replace(".pdf", "").strip().replace(" ", "_")
    return os.path.join(base_dir, safe_user, clean_book)

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "output" not in st.session_state:
    st.session_state.output = None
if "db" not in st.session_state:
    st.session_state.db = None
if "active_silo" not in st.session_state:
    st.session_state.active_silo = None

# ---------------- CONFIG & CSS ----------------
st.set_page_config(page_title="AI Tutor", layout="wide", page_icon="📘")
client = Groq(api_key="YOUR_API_KEY")

def load_css():
    if os.path.exists("styles.css"):
        with open("styles.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------------- AUTHENTICATION ----------------
if not st.session_state.logged_in:
    st.markdown('<div class="title">Smart Learning App</div>', unsafe_allow_html=True)
    st.title("📘 AI Tutor")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(u, p):
                st.session_state.user = u
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        un = st.text_input("New Username")
        pn = st.text_input("New Password", type="password")
        if st.button("Signup"):
            if signup(un, pn):
                st.success("User created")
            else:
                st.error("User exists")
    st.stop()

# ---------------- SIDEBAR (PROFILE & UPLOAD) ----------------
# import subprocess
# import os

# st.sidebar.divider()
# st.sidebar.subheader("🛠️ Vision Debugger")

# if st.sidebar.button("Run vision_test.py"):
#     with st.spinner("Running terminal script..."):
#         try:
#             # This executes your test script just like you do in the terminal
#             result = subprocess.check_output(
#                 ["python", "vision_test.py"], 
#                 stderr=subprocess.STDOUT,
#                 text=True
#             )
            
#             # Store it so we can see it in the main window
#             st.session_state.debug_vision_output = result
#             st.success("Test Script Finished!")
            
#         except Exception as e:
#             st.error(f"Failed to run script: {e}")


if "debug_vision_output" in st.session_state:
    st.markdown("### 🖥️ Terminal Output (from vision_test.py)")
    st.code(st.session_state.debug_vision_output)

with st.sidebar:
    # --- AVATAR LOGIC ---
    st.markdown(f"### 👤 {st.session_state.user}")
    avatar_file = st.file_uploader("Update Avatar", type=["png", "jpg"])
    if avatar_file:
        st.session_state.avatar = avatar_file
    
    if "avatar" in st.session_state:
        st.image(st.session_state.avatar, width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    
   # --- UPLOAD & CONFIGURATION (Collapsible) ---
# We set expanded=False so it stays closed by default
with st.expander("➕ Upload & Process New Book", expanded=False):
    st.header("Upload Book")
    pipe_mode = st.radio("Pipeline Mode", ["Academic (OCR)", "Normal (Text)"])
    
    # Hide the Index Page input if we are in Normal Mode
    if pipe_mode == "Academic (OCR)":
        index_page_num = st.number_input("Index Page", min_value=1, value=11)
    else:
        index_page_num = 1 # Not used in Normal mode
        
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        # Define the name here for NEW uploads
        clean_book_name = file.name.lower().replace(".pdf", "").strip().replace(" ", "_")
        silo_path = get_isolated_path(st.session_state.user, file.name)
        
        if st.button("Process & Index"):
            # 1. Gatekeeper: Check if book already exists
            db_check_path = os.path.join(silo_path, "vector_db")
            
            if os.path.exists(db_check_path):
                st.warning(f"⚠️ The book '{file.name}' is already indexed!")
                st.info("Select it from the 'Select Book to Study' dropdown below.")
            else:
                # 2. Proceed with Indexing
                os.makedirs(silo_path, exist_ok=True)
                pdf_save_path = os.path.join(silo_path, file.name)
                
                with open(pdf_save_path, "wb") as f:
                    f.write(file.getbuffer())

                with st.spinner("Executing Knowledge Pipeline..."):
                    # Step 1: Topic Extraction
                    if pipe_mode == "Academic (OCR)":
                        raw_topics = run_vision_test(pdf_path=pdf_save_path, index_page=index_page_num)
                        topics = [line.strip("* -") for line in raw_topics.split("\n") if line.strip()]
                        docs = load_document(pdf_save_path, is_academic=True)
                    else:
                        docs = load_document(pdf_save_path, is_academic=False)
                        topics = extract_topics(docs) # Uses the generalized topics.py logic

                    # Step 2: Database Creation
                    index = get_or_create_index(docs, st.session_state.user, clean_book_name)
                    
                    if index:
                        # Save topics BEFORE rerunning
                        with open(os.path.join(silo_path, "topics.txt"), "w", encoding="utf-8") as f:
                            f.write("\n".join(topics))
                        
                        st.session_state.db = index 
                        st.session_state.active_silo = silo_path
                        st.success("✅ Knowledge Base built and topics saved!")
                        st.rerun() 
                    else:
                        st.error("Failed to create the index.")

# ---------------- MAIN DASHBOARD ----------------
user_base = f"storage/books/{st.session_state.user}"
if not os.path.exists(user_base):
    os.makedirs(user_base)

books = [b for b in os.listdir(user_base) if os.path.isdir(os.path.join(user_base, b))]
selected_book = st.selectbox("Select Book to Study", ["None"] + books)

if selected_book != "None":
    current_clean_name = selected_book 
    current_folder = os.path.join(user_base, selected_book)
    db_path = os.path.join(current_folder, "vector_db")

    # # 1. Load Topics
    # topic_path = os.path.join(current_folder, "topics.txt")
    # book_topics = []
    # if os.path.exists(topic_path):
    #     with open(topic_path, "r", encoding="utf-8") as f:
    #         book_topics = [t.strip() for t in f.read().split("\n") if t.strip()]

    # # --- NEW: Collapsible Index Section ---
    # if book_topics:
    #     # 'expanded=False' means it is collapsed by default
    #     with st.expander("📖 View Chapter Index", expanded=False):
    #         st.write("Click a chapter to focus your study:")
            
    #         # Create the buttons inside the expander
    #         for topic in book_topics:
    #             if st.button(topic, key=f"btn_{topic}"):
    #                 st.session_state.current_topic = topic
    #                 st.toast(f"Focus set to: {topic}")
    # else:
    #     st.info("No chapter index found for this book.")

    # # 2. Auto-Load the Index (The Brain)
    # if st.session_state.db is None or st.session_state.active_silo != current_folder:
    #     if os.path.exists(db_path):
    #         with st.spinner("Re-connecting to Knowledge Base..."):
    #             from vector_db import get_or_create_index
    #             st.session_state.db = get_or_create_index([], st.session_state.user, current_clean_name)
    #             st.session_state.active_silo = current_folder
    #             print(f"✅ Auto-Loaded index for {selected_book}")
    # # --- UI LAYOUT ---

    # # --- NEW UNIFIED LAYOUT ---
    
    # # A. The Collapsible Index (Now contains the logic from col_idx)
    # if book_topics:
    #     with st.expander("📖 View Chapter Index", expanded=False):
    #         st.info("Select a chapter to focus the AI's attention:")
    #         with st.container(height=300): 
    #             for i, t in enumerate(book_topics):
    #                 # Preserving your exact session logic here
    #                 if st.button(t, key=f"unified_btn_{i}", use_container_width=True):
    #                     st.session_state.pop("current_quiz", None)
    #                     with st.spinner(f"Analyzing {t}..."):
    #                         st.session_state.current_chunks = retrieve_chunks(st.session_state.db, t)
    #                         st.session_state.output = generate_answer(st.session_state.current_chunks, f"Explain {t}")
    #                         st.session_state.mode = "topic"
    #                         st.rerun() # Refresh to show the Tutor's answer below

    # # B. The Chat Interface (Now Full Width)
    # user_q = st.chat_input("Ask a question about this book...")
    # if user_q:
    #     st.session_state.pop("current_quiz", None)
    #     with st.spinner("Searching..."):
    #         st.session_state.current_chunks = retrieve_chunks(st.session_state.db, user_q)
    #         st.session_state.output = generate_answer(st.session_state.current_chunks, user_q)
    #         st.session_state.mode = "ask"

    # # C. The Results Display (Full Width)
    # if st.session_state.output:
    #     ans_col1, ans_col2 = st.columns([1, 5])
    #     with ans_col1:
    #         if "avatar" in st.session_state:
    #             st.image(st.session_state.avatar, width=80)
    #         else:
    #             st.write("👤")
    #     with ans_col2:
    #         st.markdown(f'<div class="card"><strong>Tutor:</strong><br>{st.session_state.output}</div>', unsafe_allow_html=True)
    #         st.audio(speak_answer(st.session_state.output))
    # # col_idx, col_main = st.columns([1, 2])

    # # with col_idx:
    # #     st.subheader("📖 Chapter Index")
    # #     for i, t in enumerate(book_topics):
    # #         if st.button(t, key=f"btn_{i}", use_container_width=True):
    # #             st.session_state.pop("current_quiz", None)
    # #             with st.spinner(f"Analyzing {t}..."):
    # #                 # CONTRACT: Passing index and the topic as the query
    # #                 st.session_state.current_chunks = retrieve_chunks(st.session_state.db, t)
    # #                 st.session_state.output = generate_answer(st.session_state.current_chunks, f"Explain {t}")
    # #                 st.session_state.mode = "topic"

    # # with col_main:
    # #     user_q = st.chat_input("Ask a question about this book...")
    # #     if user_q:
    # #         st.session_state.pop("current_quiz", None)
    # #         with st.spinner("Searching..."):
    # #             # CONTRACT: Passing the session db and the user question
    # #             st.session_state.current_chunks = retrieve_chunks(st.session_state.db, user_q)
    # #             st.session_state.output = generate_answer(st.session_state.current_chunks, user_q)
    # #             st.session_state.mode = "ask"

    #     # DISPLAY RESULTS
    #     if st.session_state.output:
    #         ans_col1, ans_col2 = st.columns([1, 5])
    #         with ans_col1:
    #             if "avatar" in st.session_state:
    #                 st.image(st.session_state.avatar, width=80)
    #             else:
    #                 st.write("👤")
    #         with ans_col2:
    #             st.markdown(f'<div class="card"><strong>Tutor:</strong><br>{st.session_state.output}</div>', unsafe_allow_html=True)
    #             st.audio(speak_answer(st.session_state.output))

    #         # QUIZ SECTION
    #         with st.expander("📝 Practice Quiz"):
    #             if st.button("Generate Quiz"):
    #                 st.session_state.current_quiz = generate_quiz(st.session_state.current_chunks, "Quiz")
    #             if "current_quiz" in st.session_state:
    #                 st.markdown(st.session_state.current_quiz)

    # 1. Load Topics
    topic_path = os.path.join(current_folder, "topics.txt")
    book_topics = []
    if os.path.exists(topic_path):
        with open(topic_path, "r", encoding="utf-8") as f:
            book_topics = [t.strip() for t in f.read().split("\n") if t.strip()]

    # 2. Auto-Load the Index (The Brain)
    if st.session_state.db is None or st.session_state.active_silo != current_folder:
        if os.path.exists(db_path):
            with st.spinner("Re-connecting to Knowledge Base..."):
                from vector_db import get_or_create_index
                st.session_state.db = get_or_create_index([], st.session_state.user, current_clean_name)
                st.session_state.active_silo = current_folder
                print(f"✅ Auto-Loaded index for {selected_book}")

    # --- UNIFIED UI LAYOUT ---
    
    # A. The Single Collapsible Index (Combines display + logic)
    if book_topics:
        with st.expander("📖 View Chapter Index", expanded=False):
            st.info("Select a chapter to focus the AI's attention:")
            with st.container(height=300): 
                for i, t in enumerate(book_topics):
                    if st.button(t, key=f"unified_btn_{i}", use_container_width=True):
                        st.session_state.pop("current_quiz", None)
                        with st.spinner(f"Analyzing {t}..."):
                            st.session_state.current_chunks = retrieve_chunks(st.session_state.db, t)
                            st.session_state.output = generate_answer(st.session_state.current_chunks, f"Explain {t}")
                            st.session_state.mode = "topic"
                            st.rerun() 
    else:
        st.info("No chapter index found for this book.")

    # B. The Chat Interface (Full Width)
    user_q = st.chat_input("Ask a question about this book...")
    if user_q:
        st.session_state.pop("current_quiz", None)
        with st.spinner("Searching..."):
            st.session_state.current_chunks = retrieve_chunks(st.session_state.db, user_q)
            st.session_state.output = generate_answer(st.session_state.current_chunks, user_q)
            st.session_state.mode = "ask"

    # C. The Results Display
    if st.session_state.output:
        ans_col1, ans_col2 = st.columns([1, 5])
        with ans_col1:
            if "avatar" in st.session_state:
                st.image(st.session_state.avatar, width=80)
            else:
                st.write("👤")
        with ans_col2:
            st.markdown(f'<div class="card"><strong>Tutor:</strong><br>{st.session_state.output}</div>', unsafe_allow_html=True)
            st.audio(speak_answer(st.session_state.output))

        # D. Quiz Section (Attached to the result)
        with st.expander("📝 Practice Quiz"):
            if st.button("Generate Quiz"):
                st.session_state.current_quiz = generate_quiz(st.session_state.current_chunks, "Quiz")
            if "current_quiz" in st.session_state:
                st.markdown(st.session_state.current_quiz)