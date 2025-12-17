import streamlit as st
import pandas as pd
import json, pdfplumber, re
from docx import Document

st.set_page_config(page_title="🏠 Property Summary", page_icon="🏡", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg,#0b111f,#182235);
    color:#f5f7fa; font-family:'Segoe UI',sans-serif;
}
h2,h3 { color:#ffffff; }
thead th {
    background:#1e2a3a!important; color:#f5f7fa!important; font-weight:600;
}
tbody tr:nth-child(even){background:#162032!important;}
tbody tr:nth-child(odd){background:#101a29!important;}
hr {border:1px solid #223047;}
.dataframe-container { overflow-x:auto !important; }
.footer {text-align:center; color:#00cc66; margin-top:25px; font-size:0.85rem;}
.info-banner {
    background-color:#1a2f4c; color:#b9dcff; padding:8px 14px;
    border-radius:6px; margin-bottom:10px; font-size:0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("<h2>🏠 Property Summary Dashboard</h2>", unsafe_allow_html=True)
st.write("Upload your property files to extract and view real data summary (no fake or placeholder content).")
st.markdown("<hr>", unsafe_allow_html=True)

# ---------- File Upload ----------
uploaded_files = st.file_uploader(
    "📂 Upload property data files",
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
    """Extract simple key-value pairs from raw text."""
    lines = re.split(r'[\n;]', text)
    pairs = []
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            pairs.append((k.strip(), v.strip()))
    if not pairs:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        pairs = [(f"Line {i+1}", l) for i, l in enumerate(lines)]
    return pairs

# ---------- Processing ----------
if uploaded_files:
    summary_data = []
    file_names = [f.name for f in uploaded_files]
    selected_file = st.selectbox("Select File", file_names)

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
                rows = [(c, str(df[c].iloc[0])) for c in df.columns]
            elif ext == "txt":
                text = file.read().decode("utf-8", errors="ignore")
                rows = extract_key_values(text)
            elif ext == "docx":
                rows = extract_key_values(extract_text_from_docx(file))
            elif ext == "pdf":
                rows = extract_key_values(extract_text_from_pdf(file))
            else:
                rows = [("Content", "Unsupported")]

            df = pd.DataFrame(rows, columns=["Field", "Value"])
            df["Source File"] = file.name
            summary_data.append(df)

            if file.name == selected_file:
                st.markdown(f"### 📄 Property Details — `{file.name}`")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("<hr/>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"⚠️ Error reading {file.name}: {e}")

    # ---------- Combined Summary ----------
    if summary_data:
        st.markdown("### 📊 Property Summary (Real Data View)")
        combined_df = pd.concat(summary_data, ignore_index=True)
        combined_df.drop_duplicates(subset=["Field", "Value"], inplace=True)

        st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
        st.dataframe(combined_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>✅ Real Data Mode | Clean Extraction Enabled</div>", unsafe_allow_html=True)
else:
    st.info("⬆️ Upload property files to view full real-data summary.")
