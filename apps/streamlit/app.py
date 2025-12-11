import streamlit as st

from apps.streamlit.dashboards.config.diagnostics_page import render_config_dashboard
from apps.streamlit.dashboards.observability.diagnostics_page import (
    render_observability_dashboard,
)


def main() -> None:
    st.set_page_config(
        page_title="Quantum Control Plane",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("Quantum Control Plane")

    selection = st.sidebar.radio(
        "Sections",
        [
            "Configuration System",
            "Observability System",
        ],
        index=0,
    )

    if selection == "Configuration System":
        render_config_dashboard()

    if selection == "Observability System":
        render_observability_dashboard()


if __name__ == "__main__":
    main()
