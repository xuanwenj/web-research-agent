# Web Research Agent — CrewAI Demo

A minimal two-agent system built with [CrewAI](https://docs.crewai.com),
with a [Streamlit](https://streamlit.io) UI on top:

- **Researcher** — investigates a topic, breaks it into sub-questions, and
  searches the live web (via Tavily) to ground its findings in current
  sources rather than answering from memory alone.
- **Writer** — takes those findings and turns them into a clean,
  skimmable markdown report.

The point of this project is to see the core agentic pattern in action:
agents with defined roles, a task chain where one agent's output feeds
the next agent's input, and a tool the agent decides for itself when to
call — you can watch that decision happen in the execution log.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You'll need two API keys:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # on Windows: set ANTHROPIC_API_KEY=sk-ant-...
export TAVILY_API_KEY="tvly-..."        # free key at tavily.com
```

## Run it

**Option A — in the terminal:**

```bash
python3 research_crew.py
```

**Option B — in the browser (recommended for demos):**

```bash
streamlit run streamlit_app.py
```

This opens a simple web page: type a topic, click Run, and see the report
rendered with a download button. There's also an expandable section showing
the raw execution log, so anyone reviewing it can see exactly what the
Researcher searched for and what real results came back — not just take
your word for it.

**Running `research_crew.py` directly**, you'll see both agents "think
out loud" (that's what `verbose=True` shows you) before the final report
is printed and saved to `report_output.md`.

Try a topic you actually care about — e.g. something related to your own
job search or a technical question you've been curious about. Seeing the
Researcher's reasoning trace is the most useful part for understanding
how agentic systems actually behave.

## What to look at while it runs

- Notice the **verbose output** — it shows each agent's reasoning step by
  step. This is the "multi-step reasoning" part of agentic AI made visible.
- Notice that the Writer's task has `context=[research_task]` — this is
  how CrewAI chains agents together; no manual copy-pasting of output
  between steps.
- The Researcher has a **real web search tool** (Tavily) attached via
  `tools=[search_tool]`. Watch the verbose output for the moment it
  decides to call the tool mid-reasoning — that's the actual "agentic"
  part: it chose to search based on what it judged it didn't already
  know, rather than your code calling the search API directly.

## Suggested next steps (to go deeper)

1. **Add a third agent** — e.g. a "Critic" that reviews the Writer's
   report for factual gaps before it's finalised. This introduces
   feedback loops, a key agentic AI concept.
2. **Try rebuilding the same logic in LangGraph** once this feels
   familiar — LangGraph gives you explicit control over state and
   routing, which is a good next step once the CrewAI version clicks.
3. **Deploy the Streamlit app** (e.g. via [Streamlit Community
   Cloud](https://streamlit.io/cloud)) so it's reachable at a public
   URL, not just on `localhost`.
