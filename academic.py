import re
from pdf2image import convert_from_path
import pytesseract


def is_scanned_pdf(docs):
    sample_text = " ".join([doc.page_content for doc in docs[:3]])

    if len(sample_text.strip()) < 200:
        return True

    if sample_text.count("�") > 5:
        return True

    return False


def ocr_pdf(path):
    images = convert_from_path(path, first_page=13, last_page=13)

    pages = []

    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        print(f"🔍 OCR Page {i}:\n{text[:200]}")
        pages.append(text)

    return pages

#Academy.py

def extract_chapters_from_index(pages):
    import re

    chapters = []

    for page in pages:

        text = page if isinstance(page, str) else page.page_content
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # remove OCR garbage prefix
            line = re.sub(r"^[^A-Za-z]+", "", line)
            # normalize OCR garbage
            line = re.sub(r"[^\w\s\-\(\)]", " ", line)
            line = re.sub(r"\s+", " ", line)

            # must contain page range (strong signal)
            #if not re.search(r"\d{1,3}\s*[-–]\s*\d{1,3}", line):
             #   continue

             # relaxed pattern to catch noisy OCR lines
            if not re.search(r"[A-Za-z]{3,}", line):
                continue

            # remove page numbers
            line = re.sub(r"\d+\s*[-–]\s*\d+", "", line)

            # remove months
            line = re.sub(
                r"\b(january|february|march|april|may|june|july|august|sept|september|october|november|december)\b",
                "",
                line,
                flags=re.IGNORECASE
            )

            clean = line.strip()

            if len(clean) > 5:
                chapters.append(clean)

    return list(dict.fromkeys(chapters))


"""
def extract_chapters_from_index(pages):
    import re

#def extract_chapters_from_index(pages):

    chapters = []

    for page in pages:
        lines = page.page_content.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # ✅ Strong pattern: number + title + page range
            if re.search(r"^\d+\s+[A-Za-z].+\d+-\d+", line):

                # 🔹 remove chapter number
                line = re.sub(r"^\d+\s*", "", line)

                # 🔹 remove month + page numbers (June 1-19, Aug/Sept 106-121)
                line = re.sub(
                    r"\b(january|february|march|april|may|june|july|august|sept|september|october|november|december)[a-z/]*\s*\d+-\d+",
                    "",
                    line,
                    flags=re.IGNORECASE
                )

                # 🔹 remove leftover page numbers like 1-19
                line = re.sub(r"\d+\s*[-–]\s*\d+", "", line)

                # 🔹 remove special OCR garbage
                line = re.sub(r"[^A-Za-z\s\-]", "", line)

                # 🔹 normalize spaces
                line = re.sub(r"\s+", " ", line).strip()

                # ✅ keep meaningful titles
                if len(line) > 4:
                    print("✅ Chapter:", line)
                    chapters.append(line)

    # remove duplicates while preserving order
    return list(dict.fromkeys(chapters))
    """