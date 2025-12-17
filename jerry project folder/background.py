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