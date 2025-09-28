import streamlit as st

from quantum.bootstrap import init_observability

# Important: do the init at the very beginning
init_observability(app_name="ui_streamlit", environment="dev", namespace="quantum")

st.set_page_config(page_title="Quantum Desk", layout="wide")
st.title("Desk Quant - Supervision")
