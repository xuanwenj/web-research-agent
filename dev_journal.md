# Problems

Bugs fixed (summary list)
Blank page on Streamlit deploy — eager module-level construction. research_crew.py built LLM, TavilySearchTool, agents, tasks, and Crew at module import time. If API keys were missing, importing the module crashed before the app could render anything. Fixed by moving all construction into a build_crew() function, called lazily only when run() executes.

Import order in streamlit_app.py. The app imported research_crew before checking for missing ANTHROPIC_API_KEY/TAVILY_API_KEY, so a missing-key crash happened before the friendly error message could show. Fixed by moving the missing_keys check above the import.

Silent import failures. If from research_crew import run failed for any reason, there was no visibility into why — just a blank page. Fixed by wrapping the import in try/except and showing st.exception(e) in the UI.

Missing tavily-python dependency (the real cause of the indefinite "Starting up..." hang). requirements.txt had crewai[tools,anthropic], which installs crewai-tools but not tavily-python (that's a separate optional extra). Without it, TavilySearchTool() fell back to an interactive click.confirm("...install it?") prompt that hangs forever with no terminal to answer it. Fixed by adding tavily-python directly to requirements.txt.

streamlit.errors.NoSessionContext crash during crew execution. New progress callbacks (on_step/on_task_done) called Streamlit UI methods (status.caption(...)) from CrewAI's background thread, which doesn't have Streamlit's script context attached — this crashed the entire run the moment the first callback fired. Fixed by capturing get_script_run_ctx() on the main thread and re-attaching it via add_script_run_ctx() inside the callback.

## Bland page on Streamlit deploy

### The problem is caused by two bugs:

    - Eager construction (doing real work at import time instead of lazily inside a function) — this made the import capable of failing/crashing at all.
    - Import ordering (importing research_crew before checking for missing keys) — this meant that if it did fail, it failed before any UI existed, producing a truly blank page instead of your intended friendly error message.

Solution: made construction lazy

## Missing tavily-python dependency caused the searching process last forever

### Debug procesure

    1. Added stage-by-stage debug prints to stderr inside build_crew()/run() ("build_crew() starting", "LLM constructed", "TavilySearchTool constructed", "crew built, calling kickoff()", etc.), since stderr bypasses the redirect_stdout capture and shows up live in Streamlit Cloud's log panel.

    2. Watched the live log during a real run. It printed LLM constructed and then went completely silent for 3-5+ minutes — no further prints, no error, no crash. That pinpointed the stall to exactly one line: the TavilySearchTool() constructor call, since that's the very next statement after the last thing we saw printed.

    3. Tested that exact line locally with a deliberately fake/invalid key to see if bad credentials could cause a hang — construction completed in ~0.02 seconds. That ruled out "slow network validation inside the constructor" as the cause, since even a bad key didn't slow it down at all.

    4. Read the actual TavilySearchTool.__init__ source (via inspect.getsource) to see what it does differently when something's missing. It showed a conditional: if the tavily-python package isn't importable (TAVILY_AVAILABLE is False), it doesn't fail — it calls click.confirm("...install it? "), an interactive terminal prompt. On a server with no terminal to answer it, that call blocks forever with zero output, which matches the symptom exactly (indefinite silent hang, not a fast error).

    5. Checked whether tavily-python was actually present. Locally, pip list showed it installed — which is why my local tests never hit the bug. But scanning the full ~155-package install list from your Streamlit Cloud deploy log, tavily-python never appeared.

    6. Confirmed why it was missing from the deployed build by inspecting crewai-tools' package metadata (importlib.metadata.distribution("crewai-tools").requires) — it showed tavily-python is declared only as an optional extra (extra == 'tavily-python'), not a dependency automatically pulled in by crewai[tools].

This debug method combines local and online log - using debug prints finds out the searching stucks at the step of constructing tavilysearchtool - figuring out how tavilysearchtool works in the local environment. - check streamlit cloud deployment installation log, no tavily-python installed
