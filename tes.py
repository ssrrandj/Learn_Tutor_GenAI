from chapter_extraction import pdf_to_images, ocr_image
import re

import re

import re

import re

import cv2
import numpy as np
import pytesseract

# def test_screenshot_ocr(image_path):
#     img = cv2.imread(image_path)

#     img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

#     h, w = img.shape[:2]

#     # crop left side (chapter area)
#     img = img[int(h*0.25):int(h*0.9), int(w*0.05):int(w*0.55)]

#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     thresh = cv2.adaptiveThreshold(
#         gray, 255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         11, 2
#     )

#     config = r'--oem 3 --psm 4'

#     text = pytesseract.image_to_string(thresh, config=config)

#     print("\n===== OCR RAW OUTPUT =====\n")
#     print(text)

#     lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 3]

#     print("\n===== CLEANED LINES =====\n")
#     for line in lines:
#         print(line)

#     return lines

def extract_chapters(text):
    chapters = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            continue

        # remove junk characters at start
        line = re.sub(r'^[^A-Za-z]+', '', line)

        # keep only meaningful lines
        if len(line) < 5:
            continue

        # skip obvious non-chapter lines
        if any(word in line.lower() for word in [
            "period", "month", "page", "revision", "free", "distribution"
        ]):
            continue

        # skip pure numbers
        if re.fullmatch(r'\d+', line):
            continue

        # skip months
        if any(m in line.lower() for m in [
            "june","july","aug","sept","oct","nov","dec"
        ]):
            continue

        # ✅ MAIN RULE: must contain letters and spaces (like title)
        if re.match(r'^[A-Za-z ,\-]+$', line):
            chapters.append(line)

    # remove duplicates
    chapters = list(dict.fromkeys(chapters))

    return chapters

pdf_path = r"C:\Users\rajan\OneDrive\Desktop\Telangana-board-class-10-Physical-Science-Textbook-English-Medium.pdf"  # 👈 change this
#image = r"C:\Users\rajan\OneDrive\Pictures\physics.png"
images = pdf_to_images(pdf_path, page_number=11)

for img in images:
    print(f"\nProcessing: {img}")

    raw_text = ocr_image(img)

    print(raw_text)

    chapters = extract_chapters(raw_text)

    print("OCR OUTPUT:\n", chapters)


# if __name__ == "__main__":
#     image_path = r"C:\Users\rajan\OneDrive\Pictures\physics.png"
    
#     test_screenshot_ocr(image_path)

