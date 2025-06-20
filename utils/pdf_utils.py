import os

from fpdf import FPDF
from pypdf import PdfWriter, PdfReader

FONT_DIR = "fonts"

def create_pdf_base() -> FPDF:
    pdf = FPDF()
    pdf.add_font("UbuntuMono", "", f"{FONT_DIR}/UbuntuMono-Regular.ttf", uni=True)
    pdf.add_font("UbuntuMono", "B", f"{FONT_DIR}/UbuntuMono-Bold.ttf", uni=True)
    pdf.add_font("UbuntuMono", "I", f"{FONT_DIR}/UbuntuMono-Italic.ttf", uni=True)
    return pdf

def merge_pdf_files(original_path: str, new_path: str, output_path: str) -> None:
    writer = PdfWriter()

    # Read original PDF
    if os.path.isfile(original_path):
        with open(original_path, "rb") as f_orig:
            reader_orig = PdfReader(f_orig)
            for page in reader_orig.pages:
                writer.add_page(page)

    # Read new PDF to be merged
    with open(new_path, "rb") as f_new:
        reader_new = PdfReader(f_new)
        for page in reader_new.pages:
            writer.add_page(page)

    # Write merged result
    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    # Optionally delete the new file
    os.remove(new_path)
    print(f"Merged into '{output_path}' and deleted temporary file '{new_path}'.")