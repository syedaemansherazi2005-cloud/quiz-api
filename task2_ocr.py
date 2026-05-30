"""
Task 2 — Student Info Extraction (OCR)
Works with any image size.
"""

import re
import cv2
import numpy as np
from dataclasses import dataclass

TESS_OK = False

try:
    import easyocr
    _reader = easyocr.Reader(["en"], verbose=False)
    EASY_OK = True
except Exception:
    EASY_OK = False


@dataclass
class StudentInfo:
    name: str = "Unknown"
    reg_no: str = "Unknown"

    def to_dict(self):
        return {"name": self.name, "reg_no": self.reg_no}


def _clean_name(text: str) -> str:
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_student_info(image: np.ndarray) -> StudentInfo:
    try:
        h, w = image.shape[:2]

        # Resize to standard size first
        if h != 1100 or w != 900:
            image = cv2.resize(image, (900, 1100),
                             interpolation=cv2.INTER_CUBIC)

        # Try different region sizes
        regions_to_try = [
            image[85:185, 30:600],   # Standard region
            image[80:200, 20:650],   # Slightly larger
            image[70:220, 10:700],   # Even larger
            image[60:250, 0:750],    # Maximum region
        ]

        name = "Unknown"
        reg_no = "Unknown"

        for region in regions_to_try:
            if name != "Unknown" and reg_no != "Unknown":
                break

            # Upscale for better OCR
            region = cv2.resize(region, None, fx=3, fy=3,
                              interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            gray = cv2.fastNlMeansDenoising(gray, h=10)

            if EASY_OK:
                results = _reader.readtext(gray)

                for i, (_, text, conf) in enumerate(results):
                    # Find name after "Name:" label
                    if re.search(r"^name", text,
                                re.IGNORECASE) and conf > 0.3:
                        if i + 1 < len(results):
                            candidate = _clean_name(results[i + 1][1])
                            if len(candidate) > 3:
                                name = candidate

                    # Find name in same text as "Name:"
                    m = re.search(r"name[:\s]+(.+)", text,
                                 re.IGNORECASE)
                    if m and len(m.group(1).strip()) > 1:
                        name = _clean_name(m.group(1))

                    # Fix underscores to dashes for reg no
                    text_fixed = text.replace("_", "-").replace(" ", "")

                    # Find reg pattern FA22-BSE-041
                    m = re.search(
                        r"([A-Z]{2}\d{2}[-][A-Z]{3}[-]\d{3})",
                        text_fixed, re.IGNORECASE)
                    if m:
                        reg_no = m.group(1).upper()

                    # Find reg after label
                    m = re.search(
                        r"reg[#\s:]+([A-Z0-9\-_]+)",
                        text_fixed, re.IGNORECASE)
                    if m:
                        val = m.group(1).replace("_", "-").upper()
                        if len(val) > 3:
                            reg_no = val

                # Last resort find two word text
                if name == "Unknown":
                    for _, text, conf in results:
                        if (re.search(
                                r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", text)
                                and not re.search(
                                    r"reg|class|subject|quiz|part"
                                    r"|name|bse|ai|artificial"
                                    r"|intelligence|fill|bubble",
                                    text, re.IGNORECASE)):
                            name = _clean_name(text)
                            break

        return StudentInfo(name=name, reg_no=reg_no)

    except Exception as e:
        print(f"OCR error: {e}")
        return StudentInfo(name="Unknown", reg_no="Unknown")


if __name__ == "__main__":
    import sys
    img = cv2.imread(sys.argv[1]) if len(sys.argv) > 1 else None
    if img is None:
        print("Usage: python task2_ocr.py <image_path>")
        sys.exit(1)
    info = extract_student_info(img)
    print(info.to_dict())