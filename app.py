import streamlit as st
import fitz  # PyMuPDF
import io
import tempfile
import re
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import threading
import time

# Create FastAPI app for API endpoints
api_app = FastAPI()
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api_app.post("/api/replace")
async def replace_text_in_pdf(
    file: UploadFile = File(...),
    find_text: str = Form(...),
    replace_text: str = Form(...)
):
    """API endpoint for PDF text replacement"""
    try:
        # Read uploaded PDF
        pdf_bytes = await file.read()
        
        # Perform replacement using PyMuPDF
        result_bytes, total_replacements, details, status = advanced_pdf_replacement(
            pdf_bytes, find_text, replace_text, {
                'preserve_fonts': True,
                'preserve_colors': True,
                'case_sensitive': False,
                'whole_words': False
            }
        )
        
        if result_bytes:
            # Convert to base64 for JSON response
            pdf_base64 = base64.b64encode(result_bytes).decode('utf-8')
            
            return JSONResponse({
                "success": True,
                "pdf_base64": pdf_base64,
                "replacements": total_replacements,
                "details": details,
                "status": status
            })
        else:
            return JSONResponse({
                "success": False,
                "error": status,
                "replacements": 0
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "replacements": 0
        })

def get_font_info(span):
    """Extract detailed font information from text span"""
    font_info = {
        'name': span.get('font', 'helv'),
        'size': span.get('size', 12),
        'flags': span.get('flags', 0),
        'color': span.get('color', 0),
        'ascender': span.get('ascender', 0.8),
        'descender': span.get('descender', -0.2)
    }
    
    # Clean font name (remove subset prefix if present)
    if '+' in font_info['name']:
        font_info['clean_name'] = font_info['name'].split('+')[-1]
    else:
        font_info['clean_name'] = font_info['name']
    
    return font_info

def advanced_pdf_replacement(pdf_bytes, find_text, replace_text, options):
    """Advanced PDF replacement with maximum formatting preservation"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_replacements = 0
        replacement_details = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_replacements = 0
            
            # Get detailed text information
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            original_text = span.get("text", "")
                            
                            # Apply search options with proper regex matching
                            if options['whole_words']:
                                if options['case_sensitive']:
                                    pattern = r'\b' + re.escape(find_text) + r'\b'
                                    matches = list(re.finditer(pattern, original_text))
                                else:
                                    pattern = r'\b' + re.escape(find_text) + r'\b'
                                    matches = list(re.finditer(pattern, original_text, re.IGNORECASE))
                            else:
                                if options['case_sensitive']:
                                    matches = list(re.finditer(re.escape(find_text), original_text))
                                else:
                                    matches = list(re.finditer(re.escape(find_text), original_text, re.IGNORECASE))
                            
                            # Only process if there are actual matches
                            if matches:
                                # Get font information
                                font_info = get_font_info(span)
                                bbox = fitz.Rect(span["bbox"])
                                
                                # Perform replacement
                                if options['case_sensitive']:
                                    new_text = original_text.replace(find_text, replace_text)
                                else:
                                    new_text = re.sub(re.escape(find_text), replace_text, original_text, flags=re.IGNORECASE)
                                
                                # Count actual replacements in this span
                                replacements_in_span = len(matches)
                                page_replacements += replacements_in_span
                                
                                # Remove original text
                                page.add_redact_annot(bbox, "")
                                page.apply_redactions()
                                
                                # Insert replacement text with preserved formatting
                                insert_point = bbox.tl
                                
                                # Apply formatting options
                                font_name = font_info['clean_name'] if options['preserve_fonts'] else 'helv'
                                text_color = font_info['color'] if options['preserve_colors'] else 0
                                
                                try:
                                    page.insert_text(
                                        insert_point,
                                        new_text,
                                        fontsize=font_info['size'],
                                        fontname=font_name,
                                        color=text_color,
                                        render_mode=0
                                    )
                                except:
                                    # Fallback with basic font
                                    page.insert_text(
                                        insert_point,
                                        new_text,
                                        fontsize=font_info['size'],
                                        fontname='helv',
                                        color=text_color
                                    )
            
            if page_replacements > 0:
                replacement_details.append({
                    'page': page_num + 1,
                    'replacements': page_replacements
                })
            
            total_replacements += page_replacements
        
        # Get modified PDF bytes
        result_bytes = doc.tobytes()
        doc.close()
        
        return result_bytes, total_replacements, replacement_details, "Success"
        
    except Exception as e:
        return None, 0, [], f"Error: {str(e)}"

def start_api_server():
    """Start FastAPI server in a separate thread"""
    uvicorn.run(api_app, host="127.0.0.1", port=8001, log_level="error")

# Start API server in background thread
api_thread = threading.Thread(target=start_api_server, daemon=True)
api_thread.start()

# Give the API server time to start
time.sleep(2)

# Streamlit UI
st.set_page_config(page_title="PDF Find & Replace - Hybrid Mode", layout="wide")

st.title("🎯 PDF Find & Replace (Hybrid PyMuPDF + Foxit)")
st.markdown("**Enhanced version:** PyMuPDF backend + Foxit SDK frontend")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 API Status")
    st.success("✅ FastAPI server running on port 8001")
    st.info("🔗 API endpoint: http://localhost:8001/api/replace")
    
    st.subheader("🔧 How it works:")
    st.write("1. **Frontend:** Beautiful Foxit SDK viewer")
    st.write("2. **Backend:** PyMuPDF for real text replacement")
    st.write("3. **API:** FastAPI bridge between them")

with col2:
    st.subheader("🚀 Next Steps")
    st.write("1. Keep this Streamlit app running")
    st.write("2. Open your browser to: http://localhost:8000/foxit-test.html")
    st.write("3. Upload PDF and test find & replace")
    
    if st.button("🌐 Open Foxit Interface"):
        st.markdown("**Manual:** Go to http://localhost:8000/foxit-test.html")

st.markdown("---")
st.subheader("📝 Configuration")
st.code("""
Frontend URL: http://localhost:8000/foxit-test.html
API URL: http://localhost:8001/api/replace
Streamlit URL: http://localhost:8501 (this page)
""")

st.markdown("**Keep this window open** - it runs the API server that processes your PDFs!")
