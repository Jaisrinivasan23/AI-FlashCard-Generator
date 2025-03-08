from flask import Flask, request, jsonify, render_template
import fitz  # PyMuPDF for extracting images from PDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai

app = Flask(__name__)

# Configure Google Gemini API
GEMINI_API_KEY = "Your Gemini API Key"
genai.configure(api_key=GEMINI_API_KEY)

# Set Tesseract OCR path (Update if necessary)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Global variable to store extracted text
extracted_text = ""

# Function to extract text from scanned PDFs
def extract_text_from_pdf(pdf_file):
    global extracted_text
    extracted_text = ""  # Reset previous data
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            image = Image.open(io.BytesIO(image_data))

            # Extract text using Tesseract OCR
            text = pytesseract.image_to_string(image)
            extracted_text += text + "\n\n"  # Store all extracted text

    return extracted_text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded!"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file!"})

    extracted_text = extract_text_from_pdf(file)
    return jsonify({"message": "✅ Upload & Extraction Completed!", "preview": extracted_text[:1000]})

@app.route("/get_study_material", methods=["POST"])
def get_study_material():
    global extracted_text
    data = request.json
    topic = data.get("topic", "").lower()

    if not extracted_text:
        return jsonify({"error": "No text available. Upload a PDF first!"})

    # Search for relevant content in extracted text
    lines = extracted_text.split("\n")
    relevant_content = "\n".join([line for line in lines if topic in line.lower()])

    if not relevant_content.strip():
        return jsonify({"message": f"No content found for topic: {topic}"})

    # Summarize relevant content using Google Gemini
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"Summarize the following content in a structured and detailed manner:\n\n{relevant_content[:2000]}"
    response = model.generate_content(prompt)

    return jsonify({"topic": topic, "study_material": response.text})

if __name__ == "__main__":
    app.run(debug=True)
