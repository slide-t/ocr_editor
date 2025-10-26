
#!/usr/bin/env python3
# Enhanced Personal OCR Editor (Flask + TrOCR + Line Segmentation + Spell Correction)

import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image
import io
import cv2
import numpy as np
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from spellchecker import SpellChecker

app = Flask(__name__, static_folder='static', template_folder='templates')

MODEL_NAME = "microsoft/trocr-base-handwritten"
print(f"Loading model: {MODEL_NAME}")
processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

spell = SpellChecker()

def preprocess_image_file(file_stream):
    """Convert uploaded file to grayscale PIL image and clean up noise."""
    data = np.frombuffer(file_stream.read(), np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Binarize and denoise
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def segment_lines(binary_img):
    """Split page into individual text lines for better OCR accuracy."""
    # Invert (white background, black text)
    inv = cv2.bitwise_not(binary_img)
    proj = np.sum(inv, axis=1)
    lines = []
    start = None
    threshold = np.max(proj) * 0.05

    for i, val in enumerate(proj):
        if val > threshold and start is None:
            start = i
        elif val <= threshold and start is not None:
            end = i
            if end - start > 10:  # filter out noise
                lines.append((start, end))
            start = None
    # If still open
    if start is not None:
        lines.append((start, len(proj)))

    # Extract line images
    imgs = []
    for (y1, y2) in lines:
        line_img = binary_img[y1:y2, :]
        imgs.append(Image.fromarray(line_img))
    return imgs

def spell_correct(text):
    """Simple word-level spell correction."""
    words = text.split()
    corrected = []
    for w in words:
        if w.isalpha() and w not in spell:
            corrected.append(spell.correction(w))
        else:
            corrected.append(w)
    return " ".join(corrected)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ocr", methods=["POST"])
def ocr():
    if 'image' not in request.files:
        return jsonify({"error": "image file required"}), 400
    f = request.files['image']
    try:
        img_bin = preprocess_image_file(f.stream)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Segment into lines
    lines = segment_lines(img_bin)
    if not lines:
        return jsonify({"error": "No text lines detected"}), 400

    recognized_texts = []
    for pil_img in lines:
        pixel_values = processor(images=pil_img.convert("RGB"), return_tensors="pt").pixel_values.to(device)
        generated_ids = model.generate(pixel_values, max_length=256)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        recognized_texts.append(text.strip())

    full_text = "\n".join(recognized_texts)
    corrected_text = spell_correct(full_text)
    return jsonify({"text": corrected_text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
