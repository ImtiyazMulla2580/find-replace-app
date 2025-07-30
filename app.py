import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os

st.set_page_config(page_title="Find & Replace App", layout="centered")

st.title("🔍 Find and Replace Tool")
st.markdown("Supports **PDF**, **CSV**, **XML**, and **XPT** files")

uploaded_file = st.file_uploader("Upload a file", type=["pdf", "csv", "xml", "xpt"])
find_text = st.text_input("Word to Find")
replace_text = st.text_input("Replace With")
replace_button = st.button("Replace & Download")

def replace_in_pdf(file, find_text, replace_text):
    reader = PdfReader(file)
    writer = PdfWriter()
    for page in reader.pages:
        text = page.extract_text()
        if text:
            updated_text = text.replace(find_text, replace_text)
            writer.add_page(page)
            writer.pages[-1].extract_text = lambda: updated_text
        else:
            writer.add_page(page)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        temp.seek(0)
        return temp.name

def replace_in_csv(file, find_text, replace_text):
    df = pd.read_csv(file)
    df = df.applymap(lambda x: x.replace(find_text, replace_text) if isinstance(x, str) else x)
    return df.to_csv(index=False).encode('utf-8')

def replace_in_xml(file, find_text, replace_text):
    tree = ET.parse(file)
    root = tree.getroot()

    def recursive_replace(elem):
        if elem.text and find_text in elem.text:
            elem.text = elem.text.replace(find_text, replace_text)
        for child in elem:
            recursive_replace(child)

    recursive_replace(root)
    xml_io = BytesIO()
    tree.write(xml_io, encoding='utf-8', xml_declaration=True)
    return xml_io.getvalue()

def replace_in_xpt(file, find_text, replace_text):
    return b"This file format is not supported yet, placeholder added."

if uploaded_file and replace_button and find_text:
    file_ext = uploaded_file.name.split('.')[-1].lower()

    if file_ext == "pdf":
        result_path = replace_in_pdf(uploaded_file, find_text, replace_text)
        with open(result_path, "rb") as f:
            st.download_button("📄 Download Updated PDF", f.read(), file_name="updated.pdf", mime="application/pdf")
        os.remove(result_path)

    elif file_ext == "csv":
        csv_bytes = replace_in_csv(uploaded_file, find_text, replace_text)
        st.download_button("📄 Download Updated CSV", csv_bytes, file_name="updated.csv", mime="text/csv")

    elif file_ext == "xml":
        xml_bytes = replace_in_xml(uploaded_file, find_text, replace_text)
        st.download_button("📄 Download Updated XML", xml_bytes, file_name="updated.xml", mime="application/xml")

    elif file_ext == "xpt":
        # Real XPT support requires SAS libraries — placeholder response for now
        st.warning("XPT (SAS Transport) file replacement is not yet supported.")
    else:
        st.error("Unsupported file type.")
