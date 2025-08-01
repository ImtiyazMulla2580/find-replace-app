import streamlit as st
import pypdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import tempfile
import re

st.set_page_config(page_title="PDF Find & Replace - Working Version", layout="centered")
st.title("🔍 PDF Find & Replace (Working Version)")
st.markdown("This app extracts text from PDF, replaces words, and creates a new PDF using PyPDF + reportlab ✅")
st.info("⚠️ Note: This approach extracts text and recreates the PDF. Complex layouts may not be preserved perfectly.")

uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
find_text = st.text_input("🔍 Text to Find")
replace_text = st.text_input("✏️ Replace With")

# Advanced options
with st.expander("⚙️ Advanced Options"):
    preserve_case = st.checkbox("Preserve case sensitivity", value=True)
    whole_words_only = st.checkbox("Replace whole words only", value=False)

run_button = st.button("🔁 Replace & Download")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyPDF"""
    try:
        reader = pypdf.PdfReader(pdf_file)
        text_content = []
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            text_content.append({
                'page_num': page_num + 1,
                'text': page_text
            })
        
        return text_content, len(reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None, 0

def replace_text_in_content(text_content, find_text, replace_text, preserve_case=True, whole_words_only=False):
    """Replace text in the extracted content with advanced options"""
    updated_content = []
    total_replacements = 0
    
    for page_data in text_content:
        original_text = page_data['text']
        
        if whole_words_only:
            # Use regex for whole words only
            if preserve_case:
                pattern = r'\b' + re.escape(find_text) + r'\b'
                updated_text = re.sub(pattern, replace_text, original_text)
            else:
                pattern = r'\b' + re.escape(find_text) + r'\b'
                updated_text = re.sub(pattern, replace_text, original_text, flags=re.IGNORECASE)
        else:
            # Simple string replacement
            if preserve_case:
                updated_text = original_text.replace(find_text, replace_text)
            else:
                # Case-insensitive replacement
                pattern = re.escape(find_text)
                updated_text = re.sub(pattern, replace_text, original_text, flags=re.IGNORECASE)
        
        # Count replacements
        if preserve_case and not whole_words_only:
            replacements_on_page = original_text.count(find_text)
        else:
            # Count using regex for more complex cases
            if whole_words_only:
                pattern = r'\b' + re.escape(find_text) + r'\b'
            else:
                pattern = re.escape(find_text)
            
            flags = re.IGNORECASE if not preserve_case else 0
            replacements_on_page = len(re.findall(pattern, original_text, flags=flags))
        
        total_replacements += replacements_on_page
        
        updated_content.append({
            'page_num': page_data['page_num'],
            'text': updated_text,
            'replacements': replacements_on_page
        })
    
    return updated_content, total_replacements

def create_pdf_with_text(text_content, filename="updated.pdf"):
    """Create a new PDF with the replaced text using reportlab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 14
    
    # Custom styles
    page_header_style = ParagraphStyle(
        'PageHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor='darkblue'
    )
    
    story = []
    
    for page_data in text_content:
        if page_data['text'].strip():  # Only add pages with content
            # Add page header
            page_header = f"Page {page_data['page_num']}"
            story.append(Paragraph(page_header, page_header_style))
            
            # Clean and format text
            text = page_data['text'].strip()
            
            # Split into paragraphs (handle various line break patterns)
            paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
            
            for para in paragraphs:
                if para.strip():
                    # Clean up the paragraph text
                    clean_para = re.sub(r'\s+', ' ', para.strip())
                    # Escape special characters for reportlab
                    clean_para = clean_para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    story.append(Paragraph(clean_para, normal_style))
                    story.append(Spacer(1, 6))
            
            # Add space between pages (except for the last page)
            if page_data['page_num'] < len(text_content):
                story.append(Spacer(1, 30))
    
    # Build PDF
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

if uploaded_file and run_button:
    if not find_text:
        st.warning("Please enter text to find.")
    elif not replace_text:
        st.warning("Please enter replacement text.")
    else:
        with st.spinner("Processing PDF..."):
            # Step 1: Extract text from PDF
            text_content, total_pages = extract_text_from_pdf(uploaded_file)
            
            if text_content:
                st.success(f"✅ Successfully extracted text from {total_pages} pages")
                
                # Show extracted text statistics
                total_chars = sum(len(page['text']) for page in text_content)
                st.info(f"📊 Total characters extracted: {total_chars:,}")
                
                # Step 2: Replace text
                updated_content, total_replacements = replace_text_in_content(
                    text_content, find_text, replace_text, preserve_case, whole_words_only
                )
                
                if total_replacements > 0:
                    st.success(f"✅ Found and replaced {total_replacements} instances of '{find_text}'")
                    
                    # Show replacement summary
                    with st.expander("📊 Replacement Summary"):
                        st.write(f"**Search term:** {find_text}")
                        st.write(f"**Replacement:** {replace_text}")
                        st.write(f"**Case sensitive:** {preserve_case}")
                        st.write(f"**Whole words only:** {whole_words_only}")
                        st.write("**Replacements by page:**")
                        
                        for page_data in updated_content:
                            if page_data['replacements'] > 0:
                                st.write(f"• Page {page_data['page_num']}: {page_data['replacements']} replacements")
                    
                    # Step 3: Create new PDF
                    try:
                        pdf_buffer = create_pdf_with_text(updated_content)
                        
                        if pdf_buffer:
                            st.success("✅ New PDF created successfully!")
                            
                            # Create columns for download and preview
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.download_button(
                                    label="📥 Download Updated PDF",
                                    data=pdf_buffer,
                                    file_name=f"updated_{uploaded_file.name}",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            
                            with col2:
                                st.info("💡 The new PDF contains the extracted text with replacements applied. Layout formatting may differ from the original.")
                                
                    except Exception as e:
                        st.error(f"Error creating PDF: {str(e)}")
                        
                else:
                    st.warning(f"❌ No instances of '{find_text}' found in the document.")
                    
                    # Show suggestions
                    st.info("💡 Try adjusting your search:")
                    st.write("• Check spelling and capitalization")
                    st.write("• Try searching for partial words")
                    st.write("• Use the case-insensitive option")
                    
                # Show preview of extracted text
                with st.expander("👀 Preview Extracted Text (First 2 Pages)"):
                    for page_data in text_content[:2]:  # Show first 2 pages
                        st.subheader(f"Page {page_data['page_num']}")
                        preview_text = page_data['text'][:1000] + "..." if len(page_data['text']) > 1000 else page_data['text']
                        st.text_area(
                            f"Page {page_data['page_num']} Content", 
                            preview_text, 
                            height=200, 
                            key=f"preview_{page_data['page_num']}",
                            help="This is the raw text extracted from the PDF"
                        )
                        
                        # Highlight found instances
                        if find_text.lower() in page_data['text'].lower():
                            count = page_data['text'].lower().count(find_text.lower())
                            st.success(f"✅ Found '{find_text}' {count} times on this page")

# Add footer with instructions
st.markdown("---")
st.markdown("""
### 📝 How to Use:
1. **Upload** your PDF file
2. **Enter** the text you want to find and replace
3. **Configure** advanced options if needed
4. **Click** 'Replace & Download' to process
5. **Download** the updated PDF

### ⚠️ Important Notes:
- This tool extracts text and recreates the PDF, so complex formatting may be lost
- Images, tables, and special layouts will not be preserved
- Best suited for text-heavy documents
- Large PDFs may take longer to process
""")
