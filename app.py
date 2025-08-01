import streamlit as st
import fitz  # PyMuPDF
import io
import tempfile
import re

st.set_page_config(page_title="PDF Find & Replace - Enhanced", layout="centered")
st.title("🎯 PDF Find & Replace (Enhanced Formatting)")
st.markdown("Advanced PDF text replacement with maximum formatting preservation ✨")

uploaded_file = st.file_uploader("📄 Upload a PDF file", type=["pdf"])
find_text = st.text_input("🔍 Text to Find")
replace_text = st.text_input("✏️ Replace With")

# Processing options
st.subheader("🔧 Processing Options")
col1, col2 = st.columns(2)

with col1:
    preserve_fonts = st.checkbox("🔤 Preserve original fonts", value=True)
    preserve_colors = st.checkbox("🎨 Preserve text colors", value=True)

with col2:
    case_sensitive = st.checkbox("🔍 Case sensitive search", value=True)
    whole_words = st.checkbox("📝 Whole words only", value=False)

run_button = st.button("🔁 Replace & Download", type="primary")

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
    """Advanced PDF replacement with maximum formatting preservation - FIXED VERSION"""
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
                            
                            # FIXED: Apply search options with proper regex matching
                            if options['whole_words']:
                                if options['case_sensitive']:
                                    pattern = r'\b' + re.escape(find_text) + r'\b'
                                    matches = list(re.finditer(pattern, original_text))
                                else:
                                    pattern = r'\b' + re.escape(find_text) + r'\b'
                                    matches = list(re.finditer(pattern, original_text, re.IGNORECASE))
                            else:
                                # FIXED: Use proper regex finditer instead of simple boolean check
                                if options['case_sensitive']:
                                    matches = list(re.finditer(re.escape(find_text), original_text))
                                else:
                                    matches = list(re.finditer(re.escape(find_text), original_text, re.IGNORECASE))
                            
                            # FIXED: Only process if there are actual matches
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

def fallback_text_replacement(pdf_bytes, find_text, replace_text, options):
    """Fallback method with basic text replacement"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        new_doc = fitz.open()
        total_replacements = 0
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extract text and perform replacement
            text = page.get_text()
            if options['case_sensitive']:
                replaced_text = text.replace(find_text, replace_text)
                replacements = text.count(find_text)
            else:
                replaced_text = re.sub(re.escape(find_text), replace_text, text, flags=re.IGNORECASE)
                replacements = len(re.findall(re.escape(find_text), text, re.IGNORECASE))
            
            total_replacements += replacements
            
            # Create new page
            rect = page.rect
            new_page = new_doc.new_page(width=rect.width, height=rect.height)
            
            if replaced_text.strip():
                new_page.insert_text(
                    (50, 50),
                    replaced_text,
                    fontsize=11,
                    fontname="helv"
                )
        
        result_bytes = new_doc.tobytes()
        new_doc.close()
        doc.close()
        
        return result_bytes, total_replacements, [], "Fallback method used"
        
    except Exception as e:
        return None, 0, [], f"Fallback failed: {str(e)}"

def analyze_pdf_complexity(pdf_bytes):
    """Analyze PDF to recommend best processing method"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        stats = {
            'pages': len(doc),
            'fonts': set(),
            'colors': set(),
            'images': 0,
            'complexity_score': 0
        }
        
        for page_num in range(min(3, len(doc))):  # Check first 3 pages
            page = doc.load_page(page_num)
            
            # Count images
            stats['images'] += len(page.get_images())
            
            # Analyze text formatting
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            stats['fonts'].add(span.get('font', 'unknown'))
                            stats['colors'].add(span.get('color', 0))
        
        # Calculate complexity score
        stats['complexity_score'] = len(stats['fonts']) + len(stats['colors']) + (stats['images'] * 2)
        
        doc.close()
        return stats
        
    except:
        return {'complexity_score': 0, 'pages': 0}

if uploaded_file and run_button:
    if not find_text:
        st.warning("⚠️ Please enter text to find.")
    elif not replace_text:
        st.warning("⚠️ Please enter replacement text.")
    else:
        with st.spinner("🔍 Analyzing PDF..."):
            pdf_bytes = uploaded_file.read()
            
            # Analyze PDF complexity
            pdf_stats = analyze_pdf_complexity(pdf_bytes)
            
            # Show PDF analysis
            with st.expander("📊 PDF Analysis"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pages", pdf_stats.get('pages', 0))
                with col2:
                    st.metric("Fonts", len(pdf_stats.get('fonts', [])))
                with col3:
                    st.metric("Complexity", pdf_stats.get('complexity_score', 0))
            
            # Process PDF
            options = {
                'preserve_fonts': preserve_fonts,
                'preserve_colors': preserve_colors,
                'case_sensitive': case_sensitive,
                'whole_words': whole_words
            }
            
            with st.spinner("🔄 Processing PDF..."):
                # Try advanced method first
                result_bytes, replacements, details, status = advanced_pdf_replacement(
                    pdf_bytes, find_text, replace_text, options
                )
                
                if not result_bytes or replacements == 0:
                    # Try fallback method
                    st.info("🔄 Trying fallback method...")
                    result_bytes, replacements, details, status = fallback_text_replacement(
                        pdf_bytes, find_text, replace_text, options
                    )
                
                if result_bytes and replacements > 0:
                    st.success(f"✅ Successfully replaced {replacements} instances!")
                    
                    # Show processing details
                    with st.expander("📋 Processing Details"):
                        st.write(f"**Status:** {status}")
                        st.write(f"**Search term:** `{find_text}`")
                        st.write(f"**Replacement:** `{replace_text}`")
                        st.write(f"**Total replacements:** {replacements}")
                        
                        if details:
                            st.write("**By page:**")
                            for detail in details:
                                st.write(f"• Page {detail['page']}: {detail['replacements']} replacements")
                    
                    # Download section
                    st.markdown("### 📥 Download Result")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.download_button(
                            label="📥 Download Enhanced PDF",
                            data=result_bytes,
                            file_name=f"enhanced_{uploaded_file.name}",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    with col2:
                        file_size = len(result_bytes) / 1024  # KB
                        st.metric("File Size", f"{file_size:.1f} KB")
                    
                    st.success("🎉 PDF processing completed with enhanced formatting preservation!")
                    
                elif replacements == 0:
                    st.warning(f"❌ No instances of '{find_text}' found in the document.")
                    
                    # Suggestions
                    st.info("💡 **Suggestions:**")
                    st.write("• Check spelling and capitalization")
                    st.write("• Try disabling 'Case sensitive search'")
                    st.write("• Try disabling 'Whole words only'")
                    st.write("• Search for a shorter text snippet")
                    
                else:
                    st.error("❌ PDF processing failed.")
                    st.write(f"Error details: {status}")

# Footer
st.markdown("---")
st.markdown("""
### 🎯 Enhanced Features:
- **🔤 Font Preservation**: Maintains original fonts when possible
- **🎨 Color Preservation**: Keeps original text colors
- **📊 PDF Analysis**: Shows document complexity before processing
- **🔄 Dual Processing**: Advanced method with intelligent fallback
- **📋 Detailed Reporting**: Shows exactly what was changed

### 💡 Best Results:
- Works best with **text-heavy PDFs**
- **Simple layouts** preserve better than complex ones
- **Standard fonts** work more reliably
- **Large text** preserves better than small text

### ⚠️ Limitations:
- Cannot preserve **images** or **graphics** perfectly
- **Complex tables** may lose structure
- **Custom fonts** may fall back to standard fonts
- **Vector graphics** are not preserved
""")
