from pdf_loader import load_pdf

from chunk import paragraph_chunking

from vector_store import  create_vector_store

file_path = "data/"

chunks = paragraph_chunking(docs)

vector_db = create_vector_store(chunks)

print("vector database created successfully")

print("total chunks: ", len(chunks))