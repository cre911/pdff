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

# --- ACC Distribution Parser (Fix for Correct Price Column) ---
def parse_acc_distribution(text):
    lines = text.split("\n")  # Split the text into individual lines
    extracted_data = []

    for line in lines:
        parts = line.split()

        if len(parts) < 6:  # Ensure it's a valid line with enough data points
            continue  

        kodas = parts[0]  # First part is the product code
        qty_index = None
        price_index = None

        # Identify correct indices dynamically
        for i, part in enumerate(parts):
            if "vnt" in part:  
                qty_index = i - 1  # Quantity should be right before "vnt"
            if "," in part and qty_index is not None and i > qty_index:
                price_index = i  # First number after quantity is the unit price

        if qty_index and price_index:
            qty = parts[qty_index]
            price = parts[price_index]

            # Ensure it's formatted correctly and ignore errors
            if len(kodas) > 3 and qty.replace(",", "").isdigit():
                extracted_data.append(f"{kodas}\t{qty}\t\t{price}")

    return extracted_data

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
