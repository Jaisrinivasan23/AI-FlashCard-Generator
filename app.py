import streamlit as st
import fitz  # PyMuPDF for extracting images from PDF
import pytesseract
import google.generativeai as genai
from PIL import Image
import io

# Configure Google Gemini API (Free)
GEMINI_API_KEY = "AIzaSyDqzBpYNdc1MnM5cchcO9HJB47TAHJQzn8"
genai.configure(api_key=GEMINI_API_KEY)

# Path to Tesseract OCR (Windows users need to set this)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update this if needed

# Function to extract text from PDF images
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    extracted_text = []

    for page in doc:
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image = Image.open(io.BytesIO(image_data))

            # Extract text using Tesseract OCR
            text = pytesseract.image_to_string(image)
            extracted_text.append(text)
    
    return extracted_text

# Function to generate flashcards with Gemini
def generate_flashcards(text_chunks):
    flashcards = []
    for chunk in text_chunks[:5]:  # Process first 5 chunks to avoid long responses
        prompt = f"Extract key concepts and generate Q&A-style flashcards:\n\n{chunk[:2000]}"
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        flashcards.append(response.text)
    return flashcards

# Streamlit UI
st.title("📚 AI Flashcard Generator")
st.write("Upload a **scanned book PDF**, and I'll generate **study flashcards** ")
uploaded_file = st.file_uploader("Upload your textbook (PDF format)", type=["pdf"])

if uploaded_file:
    st.write("📖 Extracting text from book images (OCR in progress)...")
    
    # Extract Text using OCR
    extracted_text_chunks = extract_text_from_pdf(uploaded_file)
    
    if extracted_text_chunks:
        st.success("✅ OCR Completed! Generating Flashcards...")

        # Generate Flashcards
        flashcards = generate_flashcards(extracted_text_chunks)

        st.subheader("🎓 Generated Flashcards")
        for i, card in enumerate(flashcards):
            st.text_area(f"Flashcards (Batch {i+1})", card, height=300)
    else:
        st.error("❌ No text found. Try a different PDF.")

# Study Material Section
st.subheader("📌 Get Study Material on a Specific Topic")
user_query = st.text_input("Enter your topic:")
if user_query:
    combined_text = " ".join(extracted_text_chunks[:5])  # Use first few chunks
    prompt = f"Generate study material on '{user_query}' from this text:\n\n{combined_text[:2000]}"
    model = genai.GenerativeModel("gemini-pro")
    study_material = model.generate_content(prompt).text
    st.text_area("📖 Study Material:", study_material, height=200)

st.info("🔹 This app uses **Google Gemini Pro (Free Tier)** for LLM responses.")
