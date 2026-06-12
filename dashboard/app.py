"""Minimal local Streamlit shell for Dahan MarketPilot Phase 1."""

from dashboard.safety_view import safety_lines


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install Streamlit to run the local dashboard shell.") from exc

    lines = safety_lines()
    st.set_page_config(page_title="Dahan MarketPilot", layout="centered")
    st.title(lines[0])
    st.warning(lines[1])
    st.subheader(lines[2])
    st.info(lines[3])
    st.caption(lines[4])
    st.write(lines[5])


if __name__ == "__main__":
    main()
