import streamlit as st

from apps.streamlit.pages.page_observability_core import render_page


def main() -> None:
    st.set_page_config(
        page_title="Quantum Observability",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("Quantum Observability")
    selection = st.sidebar.radio(
        "Sections",
        [
            "Observability Core",
        ],
        index=0,
    )

    if selection == "Observability Core":
        render_page()


if __name__ == "__main__":
    main()
