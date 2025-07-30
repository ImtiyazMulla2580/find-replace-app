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

def process_pdf(file, find_word, replace_word):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        new_text = text.replace(find_word, replace_word)
        page.insert_text((50, 50), new_text, overlay=True)
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()

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
