import streamlit as st
import re
import os
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

st.set_page_config(page_title="PDF Find & Replace", layout="centered")

st.title("📄 PDF Find and Replace Tool")
st.write("Upload a PDF and specify words to find and replace. This tool ensures clean word-level replacement without overlaps.")

# -------------------------
# PDF Replacement Function
# -------------------------

def replace_text_in_pdf(input_pdf, replacements):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    sorted_replacements = sorted(replacements.items(), key=lambda x: -len(x[0]))

    for page in reader.pages:
        text = page.extract_text()

        if text:
            for old, new in sorted_replacements:
                pattern = r'\b{}\b'.format(re.escape(old))
                text = re.sub(pattern, new, text)

            # Create new page with updated text (keeping original layout)
            writer.add_blank_page(width=page.mediabox.width, height=page.mediabox.height)
            writer.pages[-1].merge_page(page)
        else:
            writer.add_page(page)

    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf

# -------------------------
# Streamlit App UI
# -------------------------

uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

st.markdown("### 📝 Replacement Pairs")
st.write("Enter one pair per line like: `oldword,newword`")

replacements_input = st.text_area("Find and Replace Pairs", height=150, placeholder="example,data\nerror,issue")

if st.button("Replace and Download PDF") and uploaded_file and replacements_input:
    with st.spinner("Processing..."):

        try:
            # Parse replacements
            lines = replacements_input.strip().split("\n")
            replacements = {}
            for line in lines:
                if ',' in line:
                    key, value = line.strip().split(",", 1)
                    replacements[key.strip()] = value.strip()

            output_pdf = replace_text_in_pdf(uploaded_file, replacements)

            st.success("✅ Replacement complete!")
            st.download_button("📥 Download Modified PDF", output_pdf, file_name="updated.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
else:
    st.info("👆 Upload a PDF and enter replacement pairs to begin.")
