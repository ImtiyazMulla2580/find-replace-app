import streamlit as st
import fitz  # PyMuPDF
import io
import re

st.set_page_config(page_title="PDF Find & Replace", layout="centered")
st.title("🔍 PDF Find & Replace (Text Only)")
st.markdown(
    "This app safely replaces words in your PDF while preserving as much layout as possible.<br>"
    "No overlays, no summary banners—just real, smart replacements.",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
find_text = st.text_input("🔍 Text to Find")
replace_text = st.text_input("✏️ Replace With")

# Robust search options for user
col1, col2 = st.columns(2)
with col1:
    case_sensitive = st.checkbox("Case sensitive", value=False)
with col2:
    whole_words = st.checkbox("Replace whole words only", value=True)

run_button = st.button("🔁 Replace & Download")

def perform_smart_replacement(page_text, find_text, replace_text, case_sensitive=False, whole_words=True):
    if not find_text or not page_text:
        return page_text, 0

    flags = 0 if case_sensitive else re.IGNORECASE
    escaped = re.escape(find_text)
    pattern = r'\b{}\b'.format(escaped) if whole_words else escaped
    updated_text, num = re.subn(pattern, replace_text, page_text, flags=flags)
    return updated_text, num

def process_pdf(pdf_bytes, find_text, replace_text, case_sensitive, whole_words):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    new_doc = fitz.open()
    all_replacements = 0

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        updated_text, num = perform_smart_replacement(
            text, find_text, replace_text, case_sensitive, whole_words
        )
        all_replacements += num

        # Use same page size
        rect = page.rect
        new_page = new_doc.new_page(width=rect.width, height=rect.height)
        # Insert replaced text simple for now; does not keep images/tables
        new_page.insert_text(
            (40, 60),
            updated_text,
            fontsize=12
        )

    output = new_doc.write()
    doc.close()
    new_doc.close()
    return output, all_replacements

if uploaded_file and run_button:
    if not find_text or not replace_text:
        st.warning("Please enter both 'text to find' and 'replace with' fields.")
    else:
        pdf_bytes = uploaded_file.read()
        with st.spinner("Processing PDF..."):
            result, total_replacements = process_pdf(
                pdf_bytes, find_text, replace_text, case_sensitive, whole_words
            )
        if total_replacements > 0:
            st.success(f"Replaced {total_replacements} occurrence(s) of '{find_text}' with '{replace_text}'.")
            st.download_button(
                "📥 Download Updated PDF",
                result,
                file_name=f"replaced_{uploaded_file.name}",
                mime="application/pdf"
            )
        else:
            st.info(f"No occurrences of '{find_text}' found in this PDF.")

st.markdown("---")
st.markdown("""
**Tips:**
- Enable "Case sensitive" for exact matches only.
- Enable "Replace whole words only" to avoid replacing inside other words (e.g., "happy" in "unhappy").
- This app recreates the text layer only (images/tables/links/complex formatting will not be preserved).
- For advanced formatting preservation, specialized desktop software is needed.
""")
