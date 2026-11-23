import os
import re
from pathlib import Path


class MultimodalProcessor:
    """
    Handles basic multimodal customer evidence processing.

    Supported:
    - Images
    - PDFs
    - Plain text files
    """

    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".pdf",
        ".txt"
    }

    MAX_FILE_SIZE_MB = 10

    def __init__(self):
        self.max_file_size_bytes = (
            self.MAX_FILE_SIZE_MB * 1024 * 1024
        )

    def validate_file(self, file_path):
        path = Path(file_path)

        if not path.exists():
            return {"valid": False, "reason": "FILE_NOT_FOUND"}

        if not path.is_file():
            return {"valid": False, "reason": "NOT_A_FILE"}

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            return {
                "valid": False,
                "reason": "UNSUPPORTED_FILE_TYPE",
                "extension": extension
            }

        file_size = path.stat().st_size

        if file_size <= 0:
            return {"valid": False, "reason": "EMPTY_FILE"}

        if file_size > self.max_file_size_bytes:
            return {
                "valid": False,
                "reason": "FILE_TOO_LARGE",
                "size_mb": round(file_size / (1024 * 1024), 2)
            }

        return {
            "valid": True,
            "file_name": path.name,
            "extension": extension,
            "size_bytes": file_size
        }

    def detect_file_type(self, file_path):
        extension = Path(file_path).suffix.lower()

        if extension in {".png", ".jpg", ".jpeg", ".webp"}:
            return "image"

        if extension == ".pdf":
            return "pdf"

        if extension == ".txt":
            return "text"

        return "unknown"

    def extract_text_file(self, file_path):
        path = Path(file_path)

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            return {
                "success": True,
                "text": text.strip(),
                "method": "text_reader"
            }

        except Exception as error:
            return {
                "success": False,
                "text": "",
                "method": "text_reader",
                "error": str(error)
            }

    def extract_pdf(self, file_path):
        try:
            import PyPDF2
        except ImportError:
            return {
                "success": False,
                "text": "",
                "method": "pdf",
                "error": "PyPDF2 is not installed."
            }

        try:
            reader = PyPDF2.PdfReader(file_path)
            pages = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            text = "\n".join(pages).strip()

            return {
                "success": True,
                "text": text,
                "pages": len(reader.pages),
                "method": "pdf_text_extraction"
            }

        except Exception as error:
            return {
                "success": False,
                "text": "",
                "method": "pdf_text_extraction",
                "error": str(error)
            }

    def extract_image_ocr(self, file_path):
        try:
            import pytesseract
            from PIL import Image

        except ImportError:
            return {
                "success": False,
                "text": "",
                "method": "ocr",
                "error": "pytesseract and Pillow are required."
            }

        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image).strip()

            return {
                "success": True,
                "text": text,
                "method": "tesseract_ocr"
            }

        except Exception as error:
            return {
                "success": False,
                "text": "",
                "method": "tesseract_ocr",
                "error": str(error)
            }

    def extract(self, file_path):
        validation = self.validate_file(file_path)

        if not validation.get("valid", False):
            return {
                "success": False,
                "file": validation,
                "text": "",
                "evidence": {}
            }

        file_type = self.detect_file_type(file_path)

        if file_type == "text":
            result = self.extract_text_file(file_path)

        elif file_type == "pdf":
            result = self.extract_pdf(file_path)

        elif file_type == "image":
            result = self.extract_image_ocr(file_path)

        else:
            result = {
                "success": False,
                "text": "",
                "method": "unknown",
                "error": "Unsupported file type."
            }

        result["file_name"] = Path(file_path).name
        result["file_type"] = file_type

        return result

    def extract_evidence(self, text):
        if not text:
            return {
                "order_ids": [],
                "dates": [],
                "amounts": [],
                "product_names": [],
                "error_codes": []
            }

        order_ids = re.findall(
            r"\b(?:order[\s_-]*id|order)"
            r"[\s:#-]*([A-Z0-9-]{4,})\b",
            text,
            re.IGNORECASE
        )

        dates = re.findall(
            r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b",
            text
        )

        amounts = re.findall(
            r"(?:₹|\$|€|£|Rs\.?|INR)"
            r"\s*[\d,]+(?:\.\d{1,2})?",
            text,
            re.IGNORECASE
        )

        error_codes = re.findall(
            r"\b(?:error[\s_-]*code|err)"
            r"[\s:_-]*([A-Z0-9-]{2,})\b",
            text,
            re.IGNORECASE
        )

        product_names = re.findall(
            r"\bproduct\s*:\s*(.+?)(?=\n|$)",
            text,
            re.IGNORECASE
        )

        return {
            "order_ids": order_ids,
            "dates": dates,
            "amounts": amounts,
            "product_names": product_names,
            "error_codes": error_codes
        }

    def process(self, file_path):
        result = self.extract(file_path)

        if not result.get("success", False):
            return result

        text = result.get("text", "")

        result["evidence"] = self.extract_evidence(text)

        return result