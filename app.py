import streamlit as st
from pdf2docx import Converter
from docx import Document
import os
import tempfile
# 🔧 Ensure pypandoc can use tectonic installed via packages.txt
os.environ["PATH"] += os.pathsep + "/home/adminuser/.local/bin"

st.set_page_config(page_title="PDF Find & Replace", layout="centered")
st.title("🔍 PDF Find & Replace (Preserves Layout)")
st.markdown("This app converts your PDF to Word, replaces words, and converts it back to PDF — layout preserved ✅")

uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
find_text = st.text_input("🔍 Text to Find")
replace_text = st.text_input("✏️ Replace With")
run_button = st.button("🔁 Replace & Download")

def replace_in_docx(docx_path, find_text, replace_text):
    doc = Document(docx_path)
    for para in doc.paragraphs:
        if find_text in para.text:
            inline = para.runs
            for i in range(len(inline)):
                if find_text in inline[i].text:
                    inline[i].text = inline[i].text.replace(find_text, replace_text)
    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_docx.name)
    return temp_docx.name

if uploaded_file and run_button and find_text:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        temp_pdf.flush()

        # Step 1: Convert PDF to DOCX
        temp_docx_path = temp_pdf.name.replace(".pdf", ".docx")
        cv = Converter(temp_pdf.name)
        cv.convert(temp_docx_path)
        cv.close()

        # Step 2: Replace text
        updated_docx = replace_in_docx(temp_docx_path, find_text, replace_text)

        # Step 3: Convert DOCX to PDF using tectonic (via pypandoc)
        final_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output_pdf_path = final_pdf.name

        try:
           os.system(f"pandoc {updated_docx} -o {output_pdf_path}")

            with open(output_pdf_path, "rb") as f:
                st.success("✅ Conversion successful!")
                st.download_button("📥 Download Updated PDF", f.read(), file_name="updated.pdf", mime="application/pdf")
        except Exception as e:
            st.error("❌ PDF conversion failed. Tectonic may not be installed or accessible.")
            st.exception(e)