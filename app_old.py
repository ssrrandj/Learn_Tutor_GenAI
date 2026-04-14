# import streamlit as st
# import os
# import re
# import time

# from auth import login, signup
# from pdf_loader import load_pdf
# from chunk import dynamic_chunking
# from vector_db import create_vector_store
# from retriever import retrieve_chunks
# from answer import generate_answer, generate_quiz
# from voice import speak_answer
# from embedding import get_embeddings
# from langchain_community.vectorstores import Chroma
# from groq import Groq
# from topics import extract_topics
# from academic import extract_chapters_from_index

# # ---------------- SESSION INIT ----------------
# if "mode" not in st.session_state:
#     st.session_state.mode = None

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False

# if "user" not in st.session_state:
#     st.session_state.user = None

# # ---------------- CSS ----------------
# def load_css():
#     with open("styles.css", encoding="utf-8") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# load_css()

# # ---------------- GROQ ----------------
# client = Groq(api_key="YOUR_API_KEY")

# # ---------------- LOGOUT ----------------
# def logout():
#     st.session_state.clear()
#     st.rerun()

# # ---------------- TITLE ----------------
# st.markdown('<div class="title">Smart Learning App</div>', unsafe_allow_html=True)
# st.title("📘 AI Tutor")                                                                      
# # ---------------- LOGIN ----------------
# if not st.session_state.logged_in:
#     tab1, tab2 = st.tabs(["Login", "Signup"])

#     with tab1:
#         u = st.text_input("Username")
#         p = st.text_input("Password", type="password")

#         if st.button("Login"):
#             with st.spinner("Logging in..."):
#                 if login(u, p):
#                     st.session_state.user = u
#                     st.session_state.logged_in = True
#                     st.rerun()
#                 else:
#                     st.error("Invalid login")

#     with tab2:
#         u = st.text_input("New Username")
#         p = st.text_input("New Password", type="password")

#         if st.button("Signup"):
#             with st.spinner("Signing up..."):
#                 if signup(u, p):
#                     st.success("User created")
#                 else:
#                     st.error("User exists")

#     st.stop()

# # ---------------- PATH ----------------
# BASE = f"storage/books/{st.session_state.user}"
# os.makedirs(BASE, exist_ok=True)

# @st.cache_resource
# def load_db(path):
#     return Chroma(persist_directory=path, embedding_function=get_embeddings())

# def file_clean(name):
#     return re.sub(r'[<>:"/\\|?*]', '', name)

# # ---------------- LLM TOPIC FALLBACK ----------------
# def clean_topics_with_llm(chapters):

#             prompt = f"""
# Extract chapter titles from the content.

# Rules:
# - Preserve original wording as much as possible
# - Fix obvious OCR errors (e.g., broken words, noise like 'MONK Neca elit')
# - Do NOT invent completely new topics
# - Clean and normalize text into readable chapter names
# - Ignore page numbers, months, and garbage characters

# Output:
# - Clean chapter name (Type)

# Input:
# {chr(10).join(chapters)}
# """

#             response = client.chat.completions.create(
#             model="llama3-8b-8192",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#             )

#             print("FULL RESPONSE:", response)

#             content = response.choices[0].message.content

#             if not isinstance(content, str):
#                 print("⚠️ Unexpected response:", content)
#                 return chapters  # fallback

#                 topics = content.split("\n")

#             return [t.strip("- ").strip() for t in topics if t.strip()]
# def extract_topics_with_llm(chunks):
#     sample = "\n".join(chunks[:10])

#     prompt = f"""
# Extract 5 main topics from this textbook.

# Rules:
# - Only short phrases
# - One topic per line

# Content:
# {sample}
# """

#     response = client.chat.completions.create(
#         model="llama3-8b-8192",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0
#     )

#     response = client.chat.completions.create(
#     model="meta-llama/llama-4-scout-17b-16e-instruct",
#     messages=[{"role": "user", "content": "Say hello"}],
#     temperature=0
#     )

#     print(response)

#     content = response.choices[0].message.content

#     if not content or len(content.strip()) < 10:
#         st.error("LLM returned invalid output")
#         return []

#     topics = content.split("\n")
#     return [t.strip("- ").strip() for t in topics if t.strip()]

# # ---------------- UPLOAD ----------------
# file = st.file_uploader("Upload PDF", type=["pdf"])

# if file:
#     name = file_clean(file.name.replace(".pdf", ""))
#     folder = os.path.join(BASE, name)
#     os.makedirs(folder, exist_ok=True)

#     st.session_state.path = os.path.join(folder, file.name)

#     path = st.session_state.path

#     with open(path, "wb") as f:
#         f.write(file.read())

# if st.button("Process"):

#     if "path" not in st.session_state:
#         st.warning("Upload a file first")
#         st.stop()

#     with st.spinner("Processing book..."):

#         from pdf_loader import load_pdf
#         from ocr_loader import load_pdf_ocr
#         from langchain_core.documents import Document

#         path = st.session_state.path

#         # ---------------- STEP 1: TRY NORMAL PDF ----------------
#         docs = load_pdf(path)

#         # Heuristic: if too little text → scanned PDF
#         total_text = sum(len(d.page_content.strip()) for d in docs)

#         if total_text < 500:
#             st.warning("📷 Detected scanned PDF → using OCR")

#             text_pages = load_pdf_ocr(path)
#             docs = [Document(page_content=t) for t in text_pages]

#             use_ocr = True
#         else:
#             st.success("📄 Normal PDF detected")
#             use_ocr = False

#         # ---------------- STEP 2: CHAPTER DETECTION ----------------
#         topics = []

#         if use_ocr:
#             index_pages = [docs[12]] if len(docs) > 12 else []

#             chapters = extract_chapters_from_index(index_pages)

#             if chapters and len(chapters) > 5:
#                 st.success("📚 Chapters detected from index")

#                 # 👉 Keep your LLM cleaner (but safe)
#                 topics = clean_topics_with_llm(chapters)

#             else:
#                 st.warning("⚠️ Index parsing failed → fallback")

#         # ---------------- STEP 3: FALLBACK (COMMON FOR BOTH) ----------------
#         if not topics:
#             chunks_temp = dynamic_chunking(docs)

#             topics = extract_topics(chunks_temp)

#             if not topics:
#                 st.warning("⚠️ Using LLM fallback for topics")
#                 topics = extract_topics_with_llm(chunks_temp)

#         # ---------------- STEP 4: FINAL CHUNKING ----------------
#         chunks = dynamic_chunking(docs)

#         if not chunks:
#             st.error("❌ No text extracted")
#             st.stop()

#         folder = os.path.dirname(path)

#         # ---------------- STEP 5: SAVE ----------------
#         with open(f"{folder}/topics.txt", "w", encoding="utf-8") as f:
#             f.write("\n".join(topics))

#         create_vector_store(
#             chunks,
#             os.path.join(folder, "vector_db"),
#             topics
#         )

#         st.success(f"✅ Book processed! ({len(chunks)} chunks)")
# #Replace process block
# # ---------------- SELECT BOOK ----------------
# books = os.listdir(BASE)
# book = st.selectbox("Select Book", books)

# if not book:
#     st.stop()

# folder = os.path.join(BASE, book)
# db_path = os.path.join(folder, "vector_db")

# if not os.path.exists(db_path):
#     st.warning("Process book first")
#     st.stop()

# db = load_db(db_path)

# # ---------------- LOAD TOPICS ----------------
# topics_path = os.path.join(folder, "topics.txt")

# with open(topics_path, "r", encoding="utf-8") as f:
#     topics = [t.strip() for t in f.read().split("\n") if t.strip()]

# # ---------------- DISPLAY FUNCTION ----------------
# def display_ans(answer):
    
#     col1, col2 = st.columns([1, 5])

#     with col1:
#         if "avatar" in st.session_state:
#             st.image(st.session_state.avatar, width=100)
#         else:
#             st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)

#     with col2:
#         st.markdown(f'<div class="card fade-in">', unsafe_allow_html=True)
#         st.markdown("### Answer")
#         st.markdown(f'<div class="answer">{answer}</div>', unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)
    

# # ---------------- TOPICS ----------------
# st.subheader("📖 Topics")

# for i, t in enumerate(topics):
#     if st.button(t, key=f"{t}_{i}"):
#         st.session_state.topic = t

# # ---------------- TOPIC CLICK ----------------
# if "topic" in st.session_state:
#     st.session_state.pop("current_quiz", None)

#     def clean_topic(text):
#         text = text.split(".", 1)[-1] if "." in text else text
#         text = text.split("(", 1)[0]
#         return text.strip()

#     q = f"Explain {clean_topic(st.session_state.topic)}"

#     chunks = retrieve_chunks(q, db, topics)
#     answer = generate_answer(chunks, q)

#     st.session_state.output = answer
#     st.session_state.mode = "topic"

# # ---------------- ASK ----------------
# q = st.text_input("Ask a question")

# if st.button("Ask"):
#     # clear old quiz First
#     st.session_state.pop("current_quiz", None)

#     if not q:
#         st.warning("Enter a question")
#         st.stop()

#     chunks = retrieve_chunks(q, db, topics)

#     with st.spinner("Thinking..."):
#         time.sleep(1)
#         answer = generate_answer(chunks, q)

#     st.session_state.output = answer
#     st.session_state.mode = "ask"
#     st.session_state.current_chunks = chunks

# # ---------------- FINAL DISPLAY ----------------
# if "output" in st.session_state and st.session_state.output:

#     display_ans(st.session_state.output)

#     st.audio(speak_answer(st.session_state.output))

#     if st.session_state.get("mode") == "ask":
#         with st.expander("📄 Retrieved Content"):
#             for c in st.session_state.get("current_chunks", []):
#                 st.write(c)

# # -------------------Quiz ---------- Clock

# # ---------------- QUIZ ----------------
# if "output" in st.session_state and st.session_state.output:

#      with st.expander("Quiz click to expand"):
         
#         if st.button("🧠 Generate Quiz"):
        

#             chunks = st.session_state.get("current_chunks", [])

#             if not chunks:
#                 st.warning("Ask a question first to generate quiz")
#             else:
#                 with st.spinner("Generating quiz..."):
#                     quiz = generate_quiz(
#                         chunks,
#                         st.session_state.get("current_question", "")
#                     )

#             # ✅ store quiz
#                 st.session_state.current_quiz = quiz

#     # ✅ always display quiz if exists
# if "current_quiz" in st.session_state:

#         st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
#         st.markdown("### 🧪 Quiz")
#         st.markdown(f'<div class="answer">{st.session_state.current_quiz}</div>', unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)

# with st.sidebar:
#     st.markdown("### 👤 Profile")

#     avatar_file = st.file_uploader(
#         "Upload Avatar",
#         type=["png", "jpg", "jpeg"]
#     )

#     if avatar_file:
#         st.session_state.avatar = avatar_file

#     if "avatar" in st.session_state:
#         st.image(st.session_state.avatar, width=120)

# # ---------------- LOGOUT ----------------
# with st.sidebar:
#     if st.button("Logout"):
#         logout()
#------------------------------------------
import streamlit as st
import os
import re
import time
from langchain_community.vectorstores import Chroma

# --- MODULE IMPORTS ---
from auth import login, signup
from pdf_loader import load_document
from ocr_loader import load_pdf_ocr
from chunk import dynamic_chunking
from vector_db import get_or_create_index
from retriever import retrieve_chunks
from answer import generate_answer, generate_quiz
from voice import speak_answer
from embedding import get_embeddings
from groq import Groq
from topics import extract_topics
from academic import extract_chapters_from_index
from ocr_loader import get_chapters_from_page
from llama_index.core import StorageContext, load_index_from_storage

if "last_processed_book" not in st.session_state:
    st.session_state.last_processed_book = ""



# ---------------- SESSION INIT ----------------
# Initialize session state variables if they don't exist
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest_user"  # Default fallback
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "mode" not in st.session_state:
    st.session_state.mode = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "output" not in st.session_state:
    st.session_state.output = None

# ---------------- CONFIG & CSS ----------------
st.set_page_config(page_title="AI Tutor", layout="wide")
client = Groq(api_key="YOUR_API_KEY")

def load_css():
    if os.path.exists("styles.css"):
        with open("styles.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.clear()
    st.rerun()

# ---------------- LOGIN / SIGNUP ----------------
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

# ---------------- STORAGE PATH ----------------
BASE = f"storage/books/{st.session_state.user}"
os.makedirs(BASE, exist_ok=True)

# ---------------- HELPER FUNCTIONS ----------------
@st.cache_resource
def load_db(path):
    # This must match your vector_db.py output
    if os.path.exists(os.path.join(path, "docstore.json")):
        sc = StorageContext.from_defaults(persist_dir=path)
        return load_index_from_storage(sc)
    return None

def file_clean(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

def clean_topics_with_llm(chapters):
    prompt = f"Extract and clean chapter titles from this list:\n{chr(10).join(chapters)}"
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content
    return [t.strip("- ").strip() for t in content.split("\n") if t.strip()]

# ---------------- SIDEBAR (PROFILE & UPLOAD) ----------------
import subprocess
import os

st.sidebar.divider()
st.sidebar.subheader("🛠️ Vision Debugger")

if st.sidebar.button("Run vision_test.py"):
    with st.spinner("Running terminal script..."):
        try:
            # This executes your test script just like you do in the terminal
            result = subprocess.check_output(
                ["python", "vision_test.py"], 
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Store it so we can see it in the main window
            st.session_state.debug_vision_output = result
            st.success("Test Script Finished!")
            
        except Exception as e:
            st.error(f"Failed to run script: {e}")

# --- DISPLAY THE OUTPUT ---
if "debug_vision_output" in st.session_state:
    st.markdown("### 🖥️ Terminal Output (from vision_test.py)")
    st.code(st.session_state.debug_vision_output) # Shows it in a code block for clarity
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    avatar_file = st.file_uploader("Update Avatar", type=["png", "jpg"])
    if avatar_file:
        st.session_state.avatar = avatar_file
    if "avatar" in st.session_state:
        st.image(st.session_state.avatar, width=120)
    
    st.divider()
    st.header("Upload Book")
    pipe_mode = st.radio("Pipeline Mode", ["Academic (OCR)", "Normal (Text)"])
    index_page_num = st.number_input(
        "Index Page (Table of Contents)", 
        min_value=1, value=11, 
        help="Specify the page number where the chapter list is located."
    )
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file and st.button("Process"):
        # 1. Check if this is a NEW book
        if "current_book_name" not in st.session_state:
            st.session_state.current_book_name = ""

    # 2. If the user just uploaded a DIFFERENT book, wipe the old data
        if file.name != st.session_state.current_book_name:
            st.session_state.extracted_topics = []  # Clear the list
        st.session_state.current_book_name = file.name # Update tracker
        # Optional: st.rerun() if you want the UI to refresh instantly
        name = file_clean(file.name.replace(".pdf", ""))
        folder = os.path.join(BASE, name)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, file.name)
        
        with open(path, "wb") as f:
            f.write(file.read())

        with st.spinner("Processing Knowledge Pipeline..."):
            from langchain_core.documents import Document

            if pipe_mode == "Academic (OCR)":
                # --- STEP 1: TARGETED SURGICAL EXTRACTION ---
                from ocr_loader import get_chapters_from_page
                
                with st.spinner(f"Surgically extracting index from page {index_page_num}..."):
                    # This calls our new hybrid function (fitz + gemini-2.5-flash)
                    # raw_topics_text = get_chapters_from_page(
                    #     path, 
                    #     index_page_num, 
                    #     client, 
                    #     r"C:\poppler\Library\bin"
                    # )
                    from vision_test import run_vision_test
                    print("you are executing run vision test")
                    raw_topics_text = run_vision_test()

                    # --- Replace the block around line 599 with this ---
                    #raw_topics_text = run_vision_test()

                    if raw_topics_text:
                        print(f"length of raw_topics_text:{len(raw_topics_text)}")
    # Clean and convert the string into a list
                        topics = [line.strip("* ").strip("- ").strip() 
                        for line in raw_topics_text.split("\n") 
                        if line.strip()]
                    else:
                        st.warning("Using manual fallback for chapters.")
                        raw_topics_text = "Chapter 1: Nutrition\nChapter 2: Respiration\nChapter 3: Transportation"
                        st.error("Vision test returned no data. Using fallback topic extraction.")
                        topics = [] # Or handle fallback logic
                    
                    # Clean and convert the string into a list for the rest of your pipeline
                    topics = [line.strip("* ").strip("- ").strip() 
                             for line in raw_topics_text.split("\n") 
                             if line.strip()]
                
                # Still load the full document for the vector index
                docs = load_document(path, is_academic=True)
                if docs:
        # THE SYNC POINT: Chunk the text that LlamaParse just found
                    chunks = dynamic_chunking(docs)
                    print(f"DEBUG: Created {len(chunks)} chunks from LlamaParse data.")
                else:
                    print(f"Lenght of the doc: {len(chunks)}")
            
            # if pipe_mode == "Academic (Visual)":  # Renamed from OCR
            # # --- STEP 1: VISUAL CHAPTER DISCOVERY ---
            # # Use LlamaParse to "look" at the first 20 pages specifically for the Index
            #     with st.spinner("Analyzing Book Structure (Visual Mode)..."):
            #     # We call load_document with is_academic=True
            #     # This uses LlamaParse Agentic Plus to get Markdown
            #         raw_docs = load_document(path, is_academic=True) 
                
            #     # Filter for the index range (usually pages 5-20)
            #         index_range = raw_docs[:20] 
                
            #     # extract_chapters_from_index now works on Markdown/Visual data
            #         raw_topics = extract_chapters_from_index(index_range)
                
            #     # Clean up the noise (page numbers, fragments)
            #         topics = clean_topics_with_llm(raw_topics)
            
            # # Use the parsed docs for the rest of the app
            #     docs = raw_docs
                print("You you get this topics as output")
                print("Topics retrived:", topics)

            else:
                # --- STEP 2: NORMAL FAST PATH ---
                # Uses SimpleDirectoryReader for standard text PDFs
                print("You are also in this block never leaving this block to academic block")
                docs = load_document(path, is_academic=False)
                topics = extract_topics(docs)

            chunks = dynamic_chunking(docs)
            # Use the actual user_id and the actual book name
# 'docs' are the LlamaParse documents we extracted earlier
            index = get_or_create_index(docs, st.session_state.user, name)
            
            with open(f"{folder}/topics.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(topics))
            
            st.success("✅ Ready!")
            st.rerun()

    if st.button("Logout"):
        logout()

# ---------------- MAIN DASHBOARD ----------------
books = [b for b in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, b))]
book = st.selectbox("Select Book", ["None"] + books)

if book != "None":
    folder = os.path.join(BASE, book)
    db = load_db(os.path.join(folder, "vector_db")) # This is now a LlamaIndex Index
    with open(os.path.join(folder, "topics.txt"), "r", encoding="utf-8") as f:
        topics = [t.strip() for t in f.read().split("\n") if t.strip()]

    col_idx, col_main = st.columns([1, 2])

    # LEFT: INDEX
    with col_idx:
        st.subheader("📖 Chapter Index")
        display_topics = st.session_state.get('extracted_topics', [])
        if not display_topics:
            display_topics = topics
            for i, t in enumerate(topics):
                if st.button(t, key=f"topic_{i}", use_container_width=True):
                    st.session_state.pop("current_quiz", None)
                    q = f"Explain the core concepts of the chapter: {t}"
                    with st.spinner(f"Reading about {t}..."):
                        st.session_state.current_chunks = retrieve_chunks(user_query, db)
                        st.session_state.output = generate_answer(st.session_state.current_chunks, q)
                        st.session_state.mode = "topic"

    # RIGHT: INTERACTION
    with col_main:
        user_q = st.chat_input("Ask a question about this book...")
        if user_q:
            st.session_state.pop("current_quiz", None)
            st.session_state.current_chunks = retrieve_chunks(user_query, db)
            st.session_state.output = generate_answer(st.session_state.current_chunks, user_q)
            st.session_state.mode = "ask"

        # DISPLAY RESULTS
        if st.session_state.output:
            # Display Avatar and Answer
            ans_col1, ans_col2 = st.columns([1, 4])
            with ans_col1:
                if "avatar" in st.session_state:
                    st.image(st.session_state.avatar, width=100)
                else:
                    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
            with ans_col2:
                st.markdown(f'<div class="card"><h3>Answer</h3><div class="answer">{st.session_state.output}</div></div>', unsafe_allow_html=True)
                st.audio(speak_answer(st.session_state.output))

            # QUIZ & CONTENT
            with st.expander("📝 Practice Quiz"):
                if st.button("Generate Quiz"):
                    with st.spinner("Generating..."):
                        st.session_state.current_quiz = generate_quiz(st.session_state.current_chunks, "Quiz")
                if "current_quiz" in st.session_state:
                    st.markdown(st.session_state.current_quiz)

            if st.session_state.mode == "ask":
                with st.expander("📄 Source Content"):
                    for c in st.session_state.current_chunks:
                        st.write(c)