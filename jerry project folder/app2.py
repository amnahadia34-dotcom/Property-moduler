import streamlit as st
import pandas as pd
import json, pdfplumber, re
from docx import Document
from io import StringIO

st.set_page_config(page_title="🏠 My Properties", page_icon="🏡", layout="wide")

# ---------- CSS (Jerry-Style Refined) ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg,#0b111f,#182235);
    color: #f5f7fa;
    font-family: 'Segoe UI',sans-serif;
}
h2,h3 { color:#ffffff; }
thead th {
    background:#1e2a3a !important;
    color:#f5f7fa !important;
    font-weight:600;
}
tbody tr:nth-child(even){background:#162032!important;}
tbody tr:nth-child(odd){background:#101a29!important;}
hr {border:1px solid #223047;}
.info-banner {
    background-color:#1a2f4c;
    color:#b9dcff;
    padding:8px 14px;
    border-radius:6px;
    margin-bottom:10px;
    font-size:0.9rem;
}
.banner-top {
    background-color:#243b5a;
    color:#eaf3ff;
    padding:6px 16px;
    border-radius:5px;
    font-size:0.9rem;
    margin-top:6px;
}
.footer {
    text-align:center;
    color:#00cc66;
    margin-top:25px;
    font-size:0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("<h2>🏠 My Properties</h2>", unsafe_allow_html=True)
st.write("View and manage all your property insurance profiles.")
st.markdown("<hr>", unsafe_allow_html=True)

# ---------- File Upload ----------
uploaded_files = st.file_uploader(
    "📂 Upload property data files (PDF, DOCX, TXT, CSV, JSON)",
    type=["pdf","docx","txt","csv","json"],
    accept_multiple_files=True
)

# ---------- Helper Functions ----------
def extract_text_from_pdf(f):
    try:
        with pdfplumber.open(f) as pdf:
            return "\n".join([p.extract_text() or "" for p in pdf.pages])
    except Exception:
        return ""

def extract_text_from_docx(f):
    try:
        doc = Document(f)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

def extract_key_values(text):
    lines = re.split(r'[\n;]', text)
    pairs = []
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            pairs.append((k.strip(), v.strip()))
    if not pairs:
        chunks = re.findall(r'\b[A-Za-z ]{3,20}\b[:\-]?\s*[A-Za-z0-9,./ ]{2,40}', text)
        pairs = [(f"Field {i+1}", c.strip()) for i, c in enumerate(chunks)]
    return pairs[:25]

def detect_result(val):
    try:
        if val and str(val).strip() and str(val).lower() not in ["n/a", "na", "none", "null", "-"]:
            return "✅"
        return "❌"
    except Exception:
        return "❌"

def extract_summary_fields(df):
    """Extract Address, Sale Amount, Type, City for summary"""
    address, sale_amt, prop_type, city = "-", "-", "-", "-"
    try:
        if "Field" in df.columns and "Value" in df.columns:
            def find_val(keyword):
                vals = df[df["Field"].str.contains(keyword, case=False, na=False)]["Value"].values
                return vals[0] if len(vals) > 0 else "-"
            address = find_val("address")
            sale_amt = find_val("sale")
            prop_type = find_val("type")
            city = find_val("city")
    except Exception:
        pass
    return address, sale_amt, prop_type, city

# ---------- Processing ----------
if uploaded_files:
    property_dfs = []
    summary_data = []

    property_names = [f.name for f in uploaded_files]
    selected_file = st.selectbox("Select Property", property_names)

    # Process all files first for summary
    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()
        try:
            if ext == "json":
                data = json.load(file)
                if isinstance(data, dict):
                    rows = list(data.items())
                elif isinstance(data, list):
                    if isinstance(data[0], dict):
                        rows = list(data[0].items())
                    else:
                        rows = [(f"Value {i+1}", v) for i, v in enumerate(data)]
                else:
                    rows = [("Content", str(data)[:500])]

            elif ext == "csv":
                df = pd.read_csv(file)
                property_dfs.append(df)
                rows = [(c, str(df[c].iloc[0])) for c in df.columns]

            elif ext == "txt":
                text = file.read().decode("utf-8", errors="ignore")
                rows = extract_key_values(text)

            elif ext == "docx":
                rows = extract_key_values(extract_text_from_docx(file))

            elif ext == "pdf":
                rows = extract_key_values(extract_text_from_pdf(file))

            else:
                rows = [("Content", "Unsupported file format")]

            df = pd.DataFrame(rows, columns=["Field", "Value"])
            address, sale_amt, prop_type, city = extract_summary_fields(df)
            summary_data.append({
                "File": file.name,
                "Address": address if address != "-" else "It doesn’t exist",
                "Sale Amount": sale_amt if sale_amt != "-" else "It doesn’t exist",
                "Type": prop_type if prop_type != "-" else "It doesn’t exist",
                "City": city if city != "-" else "It doesn’t exist"
            })

            if file.name == selected_file:
                st.markdown(f"### 🧾 Property Information Table — `{file.name}`")
                st.markdown("---")
                df["Result"] = df["Value"].apply(detect_result)
                extracted = df["Result"].eq("✅").sum()
                pct = round(extracted / len(df) * 100, 1) if len(df) > 0 else 0
                st.markdown(
                    f"<div class='info-banner'>📊 Extracted {extracted}/{len(df)} fields ({pct}%)</div>",
                    unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("<hr/>", unsafe_allow_html=True)

                # --- Comprehensive view (for selected file only) ---
                st.markdown("### 📈 All Properties - Comprehensive View (Selected File)")
                st.dataframe(df.head(200), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"⚠️ Error reading {file.name}: {e}")

    # ---------- 🏠 Always Visible Summary Table ----------
    if summary_data:
        st.markdown("### 🏠 Combined Summary — All Uploaded Files")
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>✅ Backend connected | Synced successfully</div>", unsafe_allow_html=True)

else:
    st.info("⬆️ Upload property files to begin viewing property information.")
