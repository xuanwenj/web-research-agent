"""
Streamlit UI for the Web Research Agent.

This file is deliberately thin: all the actual agent logic (agents, tasks,
tools) lives in research_crew.py. This file only handles displaying it in
a browser. That separation matters — if you ever swap this UI out for a
different one (a React app, an API endpoint, whatever), research_crew.py
doesn't need to change at all.

Run with:
    streamlit run streamlit_app.py
"""

import contextlib
import io
import os

import streamlit as st

from research_crew import run

st.set_page_config(page_title="Web Research Agent", page_icon="🔎")

st.title("🔎 Web Research Agent")
st.caption(
    "A two-agent CrewAI system. The **Researcher** breaks your topic into "
    "sub-questions and decides for itself when to search the live web "
    "(via Tavily) rather than answering from memory. The **Writer** turns "
    "its findings into a clean report."
)

# Fail loudly and clearly in the UI, rather than a confusing traceback,
# if the required API keys aren't set.
missing_keys = [
    k for k in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY")
    if not os.environ.get(k)
]
if missing_keys:
    st.error(
        f"Missing environment variable(s): {', '.join(missing_keys)}. "
        "Set them in your terminal before running `streamlit run streamlit_app.py`."
    )
    st.stop()

topic = st.text_input(
    "What should the crew research?",
    placeholder="e.g. The tradeoffs between LangGraph and CrewAI for agentic AI development",
)

if st.button("Run", type="primary", disabled=not topic):
    # CrewAI's verbose=True output goes to stdout via print(). We capture
    # it here so it can be shown in the UI instead of only appearing in
    # whatever terminal happens to be running the Streamlit server —
    # this is the same log you've been reading manually, just redirected.
    log_buffer = io.StringIO()

    with st.spinner("Researching and writing — this usually takes a minute or two..."):
        with contextlib.redirect_stdout(log_buffer):
            report = run(topic)

    st.success("Done!")
    st.markdown(report)

    st.download_button(
        "Download report (.md)",
        report,
        file_name="report_output.md",
        mime="text/markdown",
    )

    with st.expander("See what the agent actually did (raw execution log)"):
        st.caption(
            "This is the same kind of log you've been reading in the "
            "terminal — you can see exactly which searches it ran and "
            "what results came back."
        )
        st.text(log_buffer.getvalue())