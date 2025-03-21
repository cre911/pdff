import streamlit as st
import pdfplumber
import re

st.title("Invoice Extractor: ACC Distribution + msonic")

uploaded_file = st.file_uploader("Upload Invoice PDF", type="pdf")

# --- Profile Detection ---
def detect_supplier(text):
    if "ACC Distribution" in text:
        return "acc_distribution"
    elif "msonic Baltic OÜ" in text or "msonic.ee" in text:
        return "msonic"
    else:
        return "unknown"

# --- ACC Distribution Parser (Fix for Missing Lines) ---
def parse_acc_distribution(text):
    # Extract product codes (letters, numbers, dashes) and ensure valid data
    pattern = re.compile(
        r"(?P<kodas>[A-Za-z0-9-]+)\s+\d+\s+.*?\s+(?P<qty>\d+,\d{2})\s+vnt\s+[\d,]+\s+(?P<price>[\d,]+)"
    )
    lines = []
    for match in pattern.finditer(text):
        kodas = match.group("kodas")
        qty = match.group("qty")
        price = match.group("price")

        # Additional check to avoid skipping valid product codes
        if len(kodas) > 3 and not re.match(r"^\d{1,2}$", kodas):  
            lines.append(f"{kodas}\t{qty}\t\t{price}")
        else:
            print(f"⚠️ Skipped incorrect data: {kodas}")  # Debugging in case of missing lines
    
    return lines

# --- msonic Parser ---
def parse_msonic(text):
    pattern = re.compile(
        r"(?P<code>[A-Z0-9\-]+)\s+.*?\s+(?P<qty>\d+)\s+pc\s+(?P<price>\d+\.\d{2})"
    )
    lines = []
    for match in pattern.finditer(text):
        kodas = match.group("code")
        qty = f"{match.group('qty')},00"  # match ACC style
        price = match.group("price").replace(".", ",")  # use comma decimal
        lines.append(f"{kodas}\t{qty}\t\t{price}")
    return lines

# --- Main Extractor ---
def extract_invoice_data(pdf_file):
    all_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"

    supplier = detect_supplier(all_text)

    if supplier == "acc_distribution":
        return parse_acc_distribution(all_text)
    elif supplier == "msonic":
        return parse_msonic(all_text)
    else:
        return ["❌ Unsupported or unknown invoice format."]

# --- Streamlit Output ---
if uploaded_file:
    st.subheader("Extracted Data")
    try:
        result_lines = extract_invoice_data(uploaded_file)
        for line in result_lines:
            st.text(line)
    except Exception as e:
        st.error(f"Failed to process file: {e}")
