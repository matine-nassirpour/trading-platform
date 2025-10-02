import streamlit as st

from apps.streamlit.bootstrap import init_streamlit
from apps.streamlit.lib.obs import PageTimer, ui_action
from quantum.interface.streamlit.entrypoints import get_positions
from quantum.shared.correlation.correlation_id import get_correlation_id

# Important: do the init at the very beginning
init_streamlit()

st.set_page_config(page_title="Quantum Desk", layout="wide")
with PageTimer():
    st.title("Desk Quant - Supervision")

    # 2) Temporary stubs (while waiting for the real use cases Application)
    class _RefreshMarketStub:
        def execute(self, *, symbol: str | None = None) -> None:
            pass  # log/metrics if needed

    class _GetPositionsStub:
        def execute(self) -> list[dict]:
            return []  # returns simple dicts/DTOs for display

    refresh_uc = _RefreshMarketStub()
    positions_q = _GetPositionsStub()

    # Displays the current corr_id for debug
    st.caption(f"corr_id: {get_correlation_id() or '—'}")

    @ui_action("refresh_market")
    def on_refresh():
        refresh_uc.execute(symbol=None)

    positions = get_positions(positions_q)
    st.write(positions)
