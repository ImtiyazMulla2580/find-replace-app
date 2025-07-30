import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import zipfile
import io
import fitz  # PyMuPDF

st.title("📄 Find and Replace in Uploaded Files")

find_word = st.text_input("Find word")
replace_word = st.text_input("Replace with")
uploaded_files = st.file_uploader("Upload files (.pdf, .csv, .xml, .xpt, or .zip)", accept_multiple_files=True)

import re
from PyPDF2 import PdfReader, PdfWriter

def replace_text_in_pdf(input_path, output_path, replacements):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Sort replacements by word length (longest first) to avoid overlaps
    sorted_replacements = sorted(replacements.items(), key=lambda x: -len(x[0]))

    for page in reader.pages:
        text = page.extract_text()

        # Perform safe word-by-word replacement using word boundaries
        for old_word, new_word in sorted_replacements:
            pattern = r'\b{}\b'.format(re.escape(old_word))
            text = re.sub(pattern, new_word, text)

        writer.add_page(page)
        writer.pages[-1].extract_text = lambda: text  # Overwrite text

    with open(output_path, 'wb') as f:
        writer.write(f)


def process_csv(file, find_word, replace_word):
    df = pd.read_csv(file)
    df = df.applymap(lambda x: x.replace(find_word, replace_word) if isinstance(x, str) else x)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

def process_xml(file, find_word, replace_word):
    tree = ET.parse(file)
    root = tree.getroot()
    for elem in root.iter():
        if elem.text and find_word in elem.text:
            elem.text = elem.text.replace(find_word, replace_word)
    output = io.BytesIO()
    tree.write(output)
    return output.getvalue()

def process_file(file):
    filename = file.name.lower()
    if filename.endswith('.pdf'):
        return process_pdf(file, find_word, replace_word)
    elif filename.endswith(('.csv', '.xpt')):
        return process_csv(file, find_word, replace_word)
    elif filename.endswith('.xml'):
        return process_xml(file, find_word, replace_word)
    else:
        return None

if st.button("Process Files") and find_word and replace_word and uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as z:
        for file in uploaded_files:
            result = process_file(file)
            if result:
                z.writestr(file.name, result)
    st.download_button("Download Modified Files", zip_buffer.getvalue(), "modified_files.zip")
