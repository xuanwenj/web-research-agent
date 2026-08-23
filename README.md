# Web Research Agent — CrewAI Demo

A minimal two-agent system built with [CrewAI](https://docs.crewai.com):

- **Researcher** — investigates a topic, breaks it into sub-questions, and
  produces structured findings.
- **Writer** — takes those findings and turns them into a clean,
  skimmable markdown report.

The point of this project is to see the core agentic pattern in action:
agents with defined roles, a task chain where one agent's output feeds
the next agent's input, and (once extended) tools the agent decides for
itself when to call.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You'll need an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # on Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

## Run it

```bash
python3 research_crew.py
```

It'll ask you for a topic, then you'll see both agents "think out loud"
(that's what `verbose=True` shows you) before the final report is printed
and saved to `report_output.md`.

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
- The Researcher currently has **no tools** — it's reasoning from its own
  knowledge only. That's a deliberate simplification for this first
  version. See the comment block at the bottom of `research_crew.py` for
  how to give it real web search, which is the natural next step.

## Suggested next steps (to go deeper)

1. **Add a real search tool** (Tavily or Serper) so the Researcher can
   pull live information instead of reasoning from memory alone — this
   is what makes it a genuine *research* agent rather than a
   "reasoning-only" one.
2. **Add a third agent** — e.g. a "Critic" that reviews the Writer's
   report for factual gaps before it's finalised. This introduces
   feedback loops, a key agentic AI concept.
3. **Try rebuilding the same logic in LangGraph** once this feels
   familiar — LangGraph gives you explicit control over state and
   routing, which is a good next step once the CrewAI version clicks.
