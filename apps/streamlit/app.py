import streamlit as st

from apps.streamlit.dashboards.config.readiness_page import render_config_dashboard


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
        ],
        index=0,
    )

    if selection == "Configuration System":
        render_config_dashboard()


if __name__ == "__main__":
    main()
