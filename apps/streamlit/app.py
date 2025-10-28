import os

import streamlit as st
from opentelemetry import baggage
from opentelemetry import context as otel_context

from apps.streamlit.bootstrap import init_streamlit
from apps.streamlit.config_runtime import get_config
from apps.streamlit.lib.obs import PageTimer, ui_action
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
)
from quantum.interfaces.streamlit.entrypoints import get_positions
from quantum.shared.context.run_id import get_run_id

get_config()

st.set_page_config(page_title="Quantum Desk", layout="wide")

# Initialize the app (after set_page_config to avoid warnings)
init_streamlit()


def _current_run_id_for_ui() -> str | None:
    rid = get_run_id()
    if rid:
        return rid
    try:
        return baggage.get_baggage("run_id", context=otel_context.get_current())
    except (AttributeError, TypeError):
        return None


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
    st.caption(
        f"run_id: {_current_run_id_for_ui() or '—'}  •  corr_id: {get_correlation_id() or '—'}"
    )
    st.write("MT5 creds snapshot:", {k: v for k, v in os.environ.items() if "MT5" in k})

    @ui_action("refresh_market")
    def on_refresh():
        refresh_uc.execute(symbol=None)

    positions = get_positions(positions_q)
    st.write(positions)
