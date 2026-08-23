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
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import TavilySearchTool

# ---------------------------------------------------------------------------
# 1. Configure the LLM
#    CrewAI uses LiteLLM under the hood, so Claude models are addressed as
#    "anthropic/<model-name>". Set your API key as an environment variable
#    before running: export ANTHROPIC_API_KEY="sk-ant-..."
# ---------------------------------------------------------------------------
llm = LLM(
    model="anthropic/claude-sonnet-4-5-20250929",
    temperature=0.3,
)

# ---------------------------------------------------------------------------
# 2. Define the agents
#    Each agent gets a role, a goal, and a backstory. The backstory isn't
#    just flavour text — it shapes how the model reasons and writes when
#    acting in that role.
# ---------------------------------------------------------------------------

# The Researcher's tool: real web search. Giving an agent a `tools` list
# is what lets it decide *for itself*, mid-reasoning, when it needs to look
# something up rather than answering from memory alone.

search_tool = TavilySearchTool()

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

# ---------------------------------------------------------------------------
# 3. Define the tasks
#    Tasks are chained: the Writer's task explicitly depends on the
#    Researcher's output (via `context`), so CrewAI runs them in order
#    and passes the Researcher's result into the Writer's prompt.
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# 4. Assemble the crew and run it
# ---------------------------------------------------------------------------

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,  # researcher runs first, then writer
    verbose=True,
)


def run(topic: str) -> str:
    """Run the crew on a given topic and return the final report."""
    result = crew.kickoff(inputs={"topic": topic})
    return str(result)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Set ANTHROPIC_API_KEY before running, e.g.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
        )
    if not os.environ.get("TAVILY_API_KEY"):
        raise SystemExit(
        "Set TAVILY_API_KEY before running, e.g.\n"
        "  export TAVILY_API_KEY=tvly-...\n"
    )

    topic = input("What topic should the crew research? ").strip()
    if not topic:
        topic = "The tradeoffs between LangGraph and CrewAI for agentic AI development"

    print(f"\nRunning crew on: {topic}\n{'-' * 60}\n")
    report = run(topic)

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)

    with open("report_output.md", "w") as f:
        f.write(report)
    print("\nSaved to report_output.md")

# ---------------------------------------------------------------------------
# Adding real web search (next step, once this baseline works)
# ---------------------------------------------------------------------------
# CrewAI ships built-in tools for this. To give the Researcher agent live
# web search instead of relying on its own knowledge:
#
#   pip install 'crewai[tools]'
#
#   from crewai_tools import SerperDevTool  # or TavilySearchTool
#   search_tool = SerperDevTool()  # needs SERPER_API_KEY env var
#
#   researcher = Agent(
#       ...,
#       tools=[search_tool],
#   )
#
# That one change — giving the agent a `tools` list — is the core of what
# makes it "agentic": the agent now decides *when* to call the tool as
# part of its own reasoning, rather than you calling it for it.
