from pdf2image import convert_from_path
import pytesseract

def load_pdf_ocr(path):

    print("Started converting")

    pages = convert_from_path(
        path,
        dpi=200,
        first_page=11,
        last_page=11,
        poppler_path=r"C:\poppler\poppler-25.12.0\Library\bin"
    )

    docs = []

    for i, img in enumerate(pages):
        print(f"Processing OCR page {i+1}...")

        text = pytesseract.image_to_string(img)

        print("---- OCR OUTPUT ----")
        print(text[:500])
        print("--------------------")

        docs.append(text)
    print("coversion done")

    return docs

# Insert this at the bottom of ocr_loader.py
import fitz
from pdf2image import convert_from_path

def get_chapters_from_page(pdf_path, page_num, client, poppler_path):
    """Hybrid extraction logic to be called by app.py"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    raw_text = page.get_text().strip()
    
    if len(raw_text) > 100:
        # Digital Text Logic
        prompt = f"Extract only the chapter titles from this text. No page numbers:\n\n{raw_text}"
        response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
    else:
        # Vision Logic
        images = convert_from_path(
            pdf_path, first_page=page_num, last_page=page_num,
            poppler_path=poppler_path, dpi=200
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["List every chapter title from this image exactly. No page numbers.", images[0]]
        )
    return response.text