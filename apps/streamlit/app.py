import streamlit as st

from quantum.adapters.telemetry.correlation.correlation_id import get_correlation_id
from quantum.bootstrap import init_observability
from quantum.ui.obs import PageTimer, ui_action

# Important: do the init at the very beginning
init_observability(app_name="ui_streamlit", environment="dev", namespace="quantum")

st.set_page_config(page_title="Quantum Desk", layout="wide")
with PageTimer():
    st.title("Desk Quant - Supervision")

    # Displays the current corr_id for debug
    st.caption(f"corr_id: {get_correlation_id() or '—'}")

    @ui_action("refresh_market")
    def on_refresh():
        pass

    if st.button("Refresh market"):
        on_refresh()
