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
from database_con import init_db, save_history, load_history
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from pdf_loader_old import filter_topic_content, extract_units_with_content
from dotenv import load_dotenv

load_dotenv()


init_db() # Call this once at startup
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
client = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
Settings.llm = client
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


# if "debug_vision_output" in st.session_state:
#     st.markdown("### 🖥️ Terminal Output (from vision_test.py)")
#     st.code(st.session_state.debug_vision_output)

with st.sidebar:
    # --- AVATAR LOGIC ---
    # if "debug_vision_output" in st.session_state:
    #     st.markdown("### 🖥️ Terminal Output (from vision_test.py)")
    #     st.code(st.session_state.debug_vision_output)
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

    import shutil  # Added for folder deletion

# --- UPLOAD & CONFIGURATION (Collapsible) ---
with st.expander("➕ Upload & Process New Book", expanded=False):
    st.header("Upload Book")
    pipe_mode = st.radio("Pipeline Mode", ["Academic (OCR)", "Normal (Text)"])
    pipe_mode_Chapter_Or_Index = "Chapter"
    
    # 1. ALWAYS SHOW CONFIGURATION FIRST
    if pipe_mode == "Academic (OCR)":
        index_page_num = st.number_input("Index Page", min_value=1, value=11)
        # MOVED OUTSIDE 'if file': This ensures the radio button is visible immediately
        pipe_mode_Chapter_Or_Index = st.radio("Pipeline Index Mode", ["Chapter", "Index"])
    else:
        index_page_num = 1
        pipe_mode_Chapter_Or_Index = None # Not needed for Normal mode

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        clean_book_name = file.name.lower().replace(".pdf", "").strip().replace(" ", "_")
        silo_path = get_isolated_path(st.session_state.user, file.name)
        pdf_save_path = os.path.join(silo_path, file.name)

        # STEP 1: Verification (Only for OCR mode)
        if pipe_mode == "Academic (OCR)":
            if st.button("🔍 Check Index Content"):
                os.makedirs(silo_path, exist_ok=True)
                with open(pdf_save_path, "wb") as f:
                    f.write(file.getbuffer())
                
                with st.spinner("Vision model reading index..."):
                    raw_topics = run_vision_test(pdf_path=pdf_save_path, index_page=index_page_num)
                    # Use standard splitting for raw storage
                    st.session_state.extracted_topics = [line.strip() for line in raw_topics.split("\n") if line.strip()]

        # STEP 2: Display Results & Extract Structured Units
        if "extracted_topics" in st.session_state:
            st.markdown("### 📋 Identified Syllabus Structure")
            raw_data = st.session_state.extracted_topics
            full_text = "\n".join(raw_data) if isinstance(raw_data, list) else raw_data

            # THE FLOW DIVIDER
            if pipe_mode_Chapter_Or_Index == "Index":
                final_units = extract_units_with_content(full_text)
            else:
                raw_lines = full_text.split("\n")
                final_units = []
                noise_words = ["SYLLABUS", "INDEX", "PAGE NO", "R15A0509", "PREFACE"]
                for line in raw_lines:
                    clean = line.strip("* -")
                    if len(clean) > 5 and not any(noise in clean.upper() for noise in noise_words):
                        final_units.append(clean)

            if final_units:
                st.session_state.final_verified_topics = final_units # Prep for Step 3
                for i, item_text in enumerate(final_units):
                    st.success(f"✅ **{item_text[:50]}...**") 
                    with st.expander(f"Review Content for Item {i+1}"):
                        st.write(item_text)
            else:
                st.error("❌ Extraction Flow failed to find valid content.")

        # STEP 3: Final Indexing & Deletion Logic
        # Ensure this block is visible if topics are verified OR if it's Normal mode
        if "final_verified_topics" in st.session_state or pipe_mode == "Normal (Text)":
            st.divider()
            col_proc, col_del = st.columns(2)

            with col_proc:
                if st.button("🚀 Process & Index"):
                    db_check_path = os.path.join(silo_path, "vector_db")
                    if os.path.exists(db_check_path):
                        st.warning("⚠️ Book already indexed!")
                    else:
                        os.makedirs(silo_path, exist_ok=True)
                        # Ensure file is saved before processing
                        with open(pdf_save_path, "wb") as f:
                            f.write(file.getbuffer())

                        # START SPINNER HERE (Aligned with the button click)
                        with st.spinner("Executing Knowledge Pipeline..."):
                            topics_to_save = st.session_state.get("final_verified_topics", [])
                            docs = load_document(pdf_save_path, is_academic=(pipe_mode == "Academic (OCR)"))
                            
                            if pipe_mode == "Normal (Text)":
                                topics_to_save = extract_topics(docs)

                            index = get_or_create_index(docs, st.session_state.user, clean_book_name)
                            if index:
                                with open(os.path.join(silo_path, "topics.txt"), "w", encoding="utf-8") as f:
                                    f.write("\n".join(topics_to_save))
                                
                                st.session_state.db = index 
                                st.session_state.active_silo = silo_path
                                # Cleanup
                                for key in ["extracted_topics", "final_verified_topics"]:
                                    st.session_state.pop(key, None)
                                st.success("✅ Knowledge Base built!")
                                st.rerun()

            with col_del:
                # DELETE FUNCTIONALITY
                if st.button("🗑️ Discard & Delete"):
                    if os.path.exists(silo_path):
                        shutil.rmtree(silo_path) # Deletes the whole book folder
                    
                    # Clear session state so UI resets
                    for key in ["extracted_topics", "final_verified_topics"]:
                        if key in st.session_state: del st.session_state[key]
                    
                    st.error("Document discarded and storage cleaned.")
                    st.rerun()
    
#    # --- UPLOAD & CONFIGURATION (Collapsible) ---
# with st.expander("➕ Upload & Process New Book", expanded=False):
#     st.header("Upload Book")
#     pipe_mode = st.radio("Pipeline Mode", ["Academic (OCR)", "Normal (Text)"])
    
    
    
#     index_page_num = st.number_input("Index Page", min_value=1, value=11) if pipe_mode == "Academic (OCR)" else 1
    
#     file = st.file_uploader("Upload PDF", type=["pdf"])

#     if file:
#         # Define paths
#         clean_book_name = file.name.lower().replace(".pdf", "").strip().replace(" ", "_")
#         silo_path = get_isolated_path(st.session_state.user, file.name)
#         pdf_save_path = os.path.join(silo_path, file.name)

#         # STEP 1: Verification (Only for OCR mode)
#         if pipe_mode == "Academic (OCR)":
#             pipe_mode_Chapter_Or_Index = st.radio("Pipeline Index Mode", ["Chapter", "Index"])
#             if st.button("🔍 Check Index Content"):
#                 os.makedirs(silo_path, exist_ok=True)
#                 with open(pdf_save_path, "wb") as f:
#                     f.write(file.getbuffer())
                
#                 with st.spinner("Vision model reading index..."):
#                     raw_topics = run_vision_test(pdf_path=pdf_save_path, index_page=index_page_num)
#                     # Store the raw lines from the vision model
#                     st.write(raw_topics)
#                     # Below line is usefull in case of unit extraction
#                     #st.session_state.extracted_topics = [line.strip("* -") for line in raw_topics.split("\n") if line.strip()]
#                     # Below line is usefull in case of Chapter
#                     st.session_state.extracted_topics = raw_topics
#         # STEP 2: Display Results & Extract Structured Units
#         if "extracted_topics" in st.session_state:
#             st.markdown("### 📋 Identified Syllabus Structure")
#             full_text = "\n".join(st.session_state.extracted_topics)
#             st.write(full_text)
            
#             # Using your new multi-line extraction function
#             if pipe_mode_Chapter_Or_Index == "Index":
#                 final_units = extract_units_with_content(full_text)
#             final_units = full_text
#             # Adding experimental function revert if not worked like choosing chapter or index
#             #final_units = extract_units_with_content(full_text)
#             # Main place to concentrate ------------------
            
#             #for unit_data in full_text: Look here you made many changes if any issues
#             for unit_data in final_units:
#             #         # Show a snippet in success box, full text in expander
#                 st.success(f"✅ **{unit_data[:40]}...**") 
#                 with st.expander("View full unit topics"):
#                     st.write(unit_data)
                
#             #     # Save the high-quality units to session state
#                 st.session_state.final_verified_topics = final_units
#                 st.info("Verify the structure above. Then click 'Process & Index' below.")
#             else:
#                 st.warning("No Units found. Try a different Index Page number.")

#         # STEP 3: Final Indexing (This must be OUTSIDE the 'else' and check for final_verified_topics)
#         if "final_verified_topics" in st.session_state or pipe_mode == "Normal (Text)":
#             if st.button("🚀 Process & Index"):
#                 db_check_path = os.path.join(silo_path, "vector_db")
                
#                 if os.path.exists(db_check_path):
#                     st.warning(f"⚠️ The book '{file.name}' is already indexed!")
#                 else:
#                     os.makedirs(silo_path, exist_ok=True)
#                     if not os.path.exists(pdf_save_path):
#                         with open(pdf_save_path, "wb") as f:
#                             f.write(file.getbuffer())

#                     with st.spinner("Executing Knowledge Pipeline..."):
#                         # Use the high-quality multi-line topics we just verified
#                         topics_to_save = st.session_state.get("final_verified_topics", [])
                        
#                         docs = load_document(pdf_save_path, is_academic=(pipe_mode == "Academic (OCR)"))
                        
#                         # If Normal mode, we still need to generate topics
#                         if pipe_mode == "Normal (Text)":
#                             topics_to_save = extract_topics(docs)
#                         # need to add new function here to slip the index and chapter  
#                         index = get_or_create_index(docs, st.session_state.user, clean_book_name)
                        
#                         if index:
#                             # Save the rich multi-line topics to the silo
#                             with open(os.path.join(silo_path, "topics.txt"), "w", encoding="utf-8") as f:
#                                 f.write("\n".join(topics_to_save))
                            
#                             st.session_state.db = index 
#                             st.session_state.active_silo = silo_path
                            
#                             # Clean up session state
#                             if "extracted_topics" in st.session_state:
#                                 del st.session_state.extracted_topics
#                             if "final_verified_topics" in st.session_state:
#                                 del st.session_state.final_verified_topics
                                
#                             st.success("✅ Knowledge Base built!")
#                             st.rerun() 
#                         else:
#                             st.error("Failed to create the index.")

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
    full_history = load_history(st.session_state.user, selected_book)
    recent_memory = full_history[-4:] # Last 2 rounds of Q&A
    ans = None
    if user_q:
        st.session_state.pop("current_quiz", None)
        with st.spinner("Searching..."):
            st.session_state.current_chunks = retrieve_chunks(st.session_state.db, user_q, chat_history=recent_memory)
            st.session_state.output = generate_answer(st.session_state.current_chunks, user_q, chat_history=recent_memory)
            st.session_state.mode = "ask"
            full_history.append({"role": "user", "content": user_q})
            full_history.append({"role": "assistant", "content": ans})
            save_history(st.session_state.user, selected_book, full_history)
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