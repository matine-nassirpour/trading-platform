import streamlit as st

from apps.streamlit.bootstrap import init_streamlit
from apps.streamlit.lib.obs import PageTimer, ui_action
from quantum.interface.streamlit.entrypoints import get_positions
from quantum.shared.config.env_loader import load_env
from quantum.shared.correlation.correlation_id import get_correlation_id

load_env()  # does not overwrite existing env by default

st.set_page_config(page_title="Quantum Desk", layout="wide")

# Initialize the app (after set_page_config to avoid warnings)
init_streamlit()

with PageTimer():
    st.title("Desk Quant - Supervision")

    # Temporary Stubs
    class _RefreshMarketStub:
        def execute(self, *, symbol: str | None = None) -> None:
            pass

    class _GetPositionsStub:
        def execute(self) -> list[dict]:
            return []

    refresh_uc = _RefreshMarketStub()
    positions_q = _GetPositionsStub()

    # Displays the current corr_id (debug)
    st.caption(f"corr_id: {get_correlation_id() or '—'}")

    @ui_action("refresh_market")
    def on_refresh():
        refresh_uc.execute(symbol=None)

    positions = get_positions(positions_q)
    st.write(positions)
