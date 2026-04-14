
import google.generativeai as genai
import PIL.Image
import os

# 1. Setup your API Key (Get it free at https://aistudio.google.com/)
genai.configure(api_key="")

# 2. Initialize the model
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. Load the index image
img = PIL.Image.open(r"C:\Users\rajan\OneDrive\Pictures\physics.PNG")

# 4. Prompt for structured data (The key to "Exact" extraction)
prompt = """
Extract the textbook index from this image into a clean JSON format.
Ignore the diagonal 'SCERT TELANGANA' watermark and background colors.
Map the columns exactly: No, Chapter Title, Periods, Month, and Page No.
Return ONLY the JSON array.
"""

response = model.generate_content([prompt, img])
print(response.text)