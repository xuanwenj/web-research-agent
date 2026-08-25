"""
Web Research Agent — a small CrewAI demo project.

Two agents work together:
1. Researcher  — gathers and organises information on a topic
2. Writer      — turns the research into a clean, structured report

This version uses Claude (via the Anthropic API) as the underlying model
for both agents. No live web search is wired in yet — the Researcher
reasons from its own knowledge. See the "Adding real web search" section
at the bottom of this file for how to plug in a live search tool
(e.g. Tavily or SerpAPI) once you're ready to extend it.
"""

import os
import sys
from datetime import datetime, timezone
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import TavilySearchTool

# ---------------------------------------------------------------------------
# Everything below is built lazily inside `build_crew()` rather than at
# module import time. TavilySearchTool/LLM construction touches the
# ANTHROPIC_API_KEY/TAVILY_API_KEY env vars, so building them at import time
# means a missing key crashes the import itself — before callers (like the
# Streamlit UI) get a chance to check for missing keys and show a friendly
# error instead of a blank page.
# ---------------------------------------------------------------------------


def build_crew(on_step=None, on_task_done=None) -> tuple[Crew, list[int]]:
    """Construct the LLM, agents, tasks, and crew.

    Returns `(crew, search_call_count)`: `search_call_count` is a one-item
    list holding the number of tool (web search) calls made so far, updated
    live as the crew runs and readable by the caller once `kickoff()` is
    done.

    `on_step` (optional) is called with a short string every time an agent
    takes an action (thinking, calling a tool, etc). `on_task_done` (optional)
    is called with a short string whenever a task (research or writing)
    finishes. Both let a caller like the Streamlit UI show live progress
    instead of one long, silent spinner.
    """
    print("[research_crew] build_crew() starting", file=sys.stderr)
    # CrewAI uses LiteLLM under the hood, so Claude models are addressed as
    # "anthropic/<model-name>". Set your API key as an environment variable
    # before running: export ANTHROPIC_API_KEY="sk-ant-..."
    llm = LLM(
        model="anthropic/claude-sonnet-4-5-20250929",
        temperature=0.3,
    )
    print("[research_crew] LLM constructed", file=sys.stderr)

    # The Researcher's tool: real web search. Giving an agent a `tools` list
    # is what lets it decide *for itself*, mid-reasoning, when it needs to
    # look something up rather than answering from memory alone.
    search_tool = TavilySearchTool()
    print("[research_crew] TavilySearchTool constructed", file=sys.stderr)

    researcher = Agent(
        role="Research Analyst",
        goal="Investigate {topic} thoroughly and produce well-organised, "
             "factual findings with clear sub-points, grounded in current "
             "web sources rather than memory alone",
        backstory=(
            "You are a meticulous research analyst. You break topics down "
            "into logical sub-questions, and you use web search to check "
            "facts and find current information rather than relying only "
            "on what you already know. You flag anything you're uncertain "
            "about rather than guessing."
        ),
        llm=llm,
        tools=[search_tool],
        verbose=True,
    )

    writer = Agent(
        role="Report Writer",
        goal="Turn raw research findings into a clear, well-structured report "
             "that a busy reader could skim in two minutes",
        backstory=(
            "You are a skilled technical writer. You take dense research "
            "notes and reshape them into a report with a short summary, "
            "clear headings, and concise bullet points. You never pad "
            "the writing with filler."
        ),
        llm=llm,
        verbose=True,
    )

    # Tasks are chained: the Writer's task explicitly depends on the
    # Researcher's output (via `context`), so CrewAI runs them in order
    # and passes the Researcher's result into the Writer's prompt.
    research_task = Task(
        description=(
            "Research the topic: {topic}\n\n"
            "Break it into 3-5 key sub-questions, and answer each one with "
            "specific, factual points. Note any areas of genuine uncertainty "
            "or debate rather than presenting them as settled."
        ),
        expected_output=(
            "A structured set of findings: one heading per sub-question, "
            "with 2-4 factual bullet points under each."
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            "Using the research findings, write a short report on {topic}.\n\n"
            "Structure:\n"
            "1. A 2-3 sentence executive summary\n"
            "2. One section per sub-question, with clear headings\n"
            "3. A short 'Open questions' section if the research flagged any "
            "uncertainty\n\n"
            "Keep it skimmable — use headings and bullets, not dense paragraphs."
        ),
        expected_output="A polished markdown report, ready to share.",
        agent=writer,
        context=[research_task],
    )

    # These wrap the caller's callbacks defensively: CrewAI's step/task
    # objects can vary between versions, so we don't want a callback
    # failure to crash an otherwise-successful run.
    # Printed to stderr (not stdout) so it bypasses the Streamlit UI's
    # stdout capture and shows up live in the server-side logs for debugging.
    # Counts tool calls (i.e. live web searches) made during the run.
    # A one-item list, not a plain int, so the closure below can mutate it.
    search_call_count = [0]

    def _step_callback(step):
        try:
            role = getattr(getattr(step, "agent", None), "role", None)
            tool = getattr(step, "tool", None)
            if tool:
                search_call_count[0] += 1
            message = (
                f"{role or 'Agent'} is using tool: {tool}"
                if tool
                else f"{role or 'Agent'} is thinking..."
            )
        except Exception:
            message = "Working..."
        print(f"[research_crew] {message}", file=sys.stderr)
        if on_step:
            on_step(message)

    def _task_callback(output):
        try:
            agent_role = getattr(output, "agent", None)
            message = f"Finished: {agent_role or 'a task'}"
        except Exception:
            message = "Finished a task"
        print(f"[research_crew] {message}", file=sys.stderr)
        if on_task_done:
            on_task_done(message)

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,  # researcher runs first, then writer
        verbose=True,
        # Always registered (regardless of on_step) so search_call_count
        # stays accurate even when the caller doesn't want progress updates.
        step_callback=_step_callback,
        task_callback=_task_callback if on_task_done else None,
    )
    return crew, search_call_count


def run(topic: str, on_step=None, on_task_done=None) -> str:
    """Run the crew on a given topic and return the final report.

    `on_step`/`on_task_done` are optional progress callbacks — see
    `build_crew` for details.
    """
    print(f"[research_crew] run() called with topic={topic!r}", file=sys.stderr)
    crew, search_call_count = build_crew(on_step=on_step, on_task_done=on_task_done)
    print("[research_crew] crew built, calling kickoff()", file=sys.stderr)
    result = crew.kickoff(inputs={"topic": topic})
    print("[research_crew] kickoff() finished", file=sys.stderr)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    footer = (
        f"\n\n---\n"
        f"*This report includes live web search results, last updated {timestamp}.*\n"
        f"*Grounded in {search_call_count[0]} live web source"
        f"{'s' if search_call_count[0] != 1 else ''}.*"
    )
    return str(result) + footer


# That one change — giving the agent a `tools` list — is the core of what
# makes it "agentic": the agent now decides *when* to call the tool as
# part of its own reasoning, rather than you calling it for it.
