# Build Spec: AI Mystery Detective Team

Port the working Colab notebook (`AI_Mystery_Detective_Team.ipynb`) into a proper
local Python project. Preserve the existing logic exactly — this is a restructure,
not a redesign. Add one feature: a case-variant comparison run.

## Source of truth
- Agent roles, case file text, and handoff order come from the uploaded notebook
  and case book. Do not invent new agents or change the sequence.
- Model: `gemini-2.5-flash-lite` via the `google-genai` SDK (`from google import genai`).
- Handoff order (fixed): `Detective → Evidence → Suspect → Skeptic → Chief`

## Project structure

```
ai-mystery-detectives/
├── case_file.py       # CASE_FILE constant + a CASE_FILE_VARIANT with Evidence E removed
├── agents.py           # AGENTS dict (role -> instruction) + ask_agent()
├── investigate.py      # investigate() orchestration, sequential, builds shared_context
├── app.py               # Gradio UI
├── requirements.txt
├── .env.example
└── README.md
```

## case_file.py
- Move `CASE_FILE` string verbatim from the notebook.
- Add `CASE_FILE_VARIANT`: identical text but with Evidence item **E** (blue velvet
  fibers) removed, per the case book's own "Investigation Challenge" — Evidence
  Register entry E and its row in the Evidence Classification table.
- Export both as named constants, no other changes.

## agents.py
- Move the `AGENTS` dict verbatim (Detective, Evidence, Suspect, Skeptic, Chief
  and their exact instruction strings from the notebook).
- Move `ask_agent(name, instruction, case_file, shared_context)` — same prompt
  template as the notebook, but take `case_file` as a parameter instead of a
  closure over a global, so it can run against either `CASE_FILE` or
  `CASE_FILE_VARIANT`.
- Client init: read `GEMINI_API_KEY` from environment (via `python-dotenv`),
  not Colab Secrets. Raise a clear error if missing.

## investigate.py
- `run_investigation(case_file, progress_callback=None) -> dict[str, str]`:
  same loop as the notebook's `investigate()`, agent order fixed, building
  `shared_context` from prior reports as it goes. No loop-back, no revision —
  each agent runs once, in order, same as the source.
- Keep it Gradio-independent so it's testable outside the UI.

## app.py (Gradio)
Two tabs:
1. **Investigation** — same as the notebook: case file accordion (read-only),
   "Start Investigation" button, one Markdown output per agent.
2. **Compare Runs** — runs `run_investigation` against `CASE_FILE` and
   `CASE_FILE_VARIANT` side by side (two columns), so the user can do the case
   book's own "remove Evidence E" exercise without manually editing code and
   rerunning. Show Chief's final verdict from each run stacked for comparison.

Use `demo.launch()` (no `share=True` — this now runs locally, not in Colab).

## requirements.txt
```
google-genai
gradio
python-dotenv
```

## .env.example
```
GEMINI_API_KEY=your_key_here
```

## README.md
- How to get a Gemini API key (AI Studio), copy `.env.example` to `.env`, install
  requirements, run `python app.py`.
- One line noting the case is fictional and the intended answer (for facilitators
  only) is documented in the source case book, not in this repo.

## Explicit non-goals
- No CrewAI/LangGraph — the notebook's direct prompt-chaining approach works and
  matches the case book's fixed 5-agent sequential design.
- No agent-generated case content — the case file is fixed, with a known
  facilitator answer key, so runs stay comparable.
- No loop-back/revision cycle between agents — Skeptic critiques once, Chief
  synthesizes once, matching `Detective → Evidence → Suspect → Skeptic → Chief`.
