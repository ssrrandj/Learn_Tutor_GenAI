import fitz  # PyMuPDF
import requests
import cv2
import numpy as np
import os
import pytesseract

pytesseract.pytesseract.tesseract_cmd =  r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------------------
# STEP 1: Convert PDF to images
# -------------------------------
def pdf_to_images(pdf_path, page_number=11):
    import fitz  # PyMuPDF

    pdf = fitz.open(pdf_path)

    page = pdf[page_number - 1]   # page index starts from 0

    pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
    img_path = f"page_{page_number}.png"
    pix.save(img_path)

    return [img_path]


# -------------------------------
# STEP 2: Preprocess image
# -------------------------------
def preprocess_image(img_path):
    img = cv2.imread(img_path)

    if img is None:
        return img_path

    height, width, _ = img.shape

    # crop left side
    img = img[:, :int(width * 0.7)]

    # convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔥 CLAHE (boost contrast for colored backgrounds)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # adaptive threshold (better than fixed)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    clean_path = "clean_" + img_path
    cv2.imwrite(clean_path, thresh)

    return clean_path


# -------------------------------
# STEP 3: OCR using API
# -------------------------------
def ocr_image(image_path):
    img = cv2.imread(image_path)

    # resize
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    h, w = img.shape[:2]

    # crop chapter area
    img = img[int(h*0.30):int(h*0.85), int(w*0.05):int(w*0.50)]

    # 🔥 convert to LAB color space (better for contrast)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # 🔥 enhance light channel
    l = cv2.equalizeHist(l)

    lab = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # grayscale
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)

    # 🔥 strong threshold (important)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    config = r'--oem 3 --psm 4'

    text = pytesseract.image_to_string(thresh, config=config)

    return text