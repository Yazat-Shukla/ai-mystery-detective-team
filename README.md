# AI Mystery Detective Team

A local Python and Gradio application featuring five specialized AI agents investigating a fictional mystery case using sequential prompt handoffs, deterministic evidence validation, and automated quality control auditing.

---

## Architecture Diagram

```text
               CASE FILE (CASE_FILE or CASE_FILE_VARIANT)
                                  │
                                  ▼
                            1. Detective Agent
                                  │
                                  ▼
                            2. Evidence Agent
                                  │
                                  ▼
                      [ Structured Evidence Parsing ]
                                  │
                                  ▼
                      3. Python Evidence Validator (validator.py)
                       - Extracts Valid Case Evidence IDs
                       - Parses & Validates FACT / INFERENCE / DISTRACTION
                       - Parses Machine-Parseable SUSPECT_POSITION Lines
                       - Calculates Deterministic Net Evidence Positions
                         (net = implicating_facts - supporting_facts)
                                  │
                                  ▼
                             4. Suspect Agent
                                  │
                                  ▼
                             5. Skeptic Agent
                                  │
                                  ▼
             [ Validated Evidence Metrics + Prior Reports ]
                                  │
                                  ▼
                              6. Chief Agent
                                  │
                                  ▼
                       7. Python Audit Checklist Layer (audit.py)
                       - Validates Citations & Suspect References
                       - Checks Alignment Between Net Facts & Chief Confidence
                       - Verifies Uncertainty & Alternative Theories
                                  │
                                  ▼
                         Gradio UI (2 Tabs)
                       - Workshop Agent Markdown Reports
                       - Evidence Lineage & Suspect Matrix
                       - Python Audit Checklist & Verdict Status
                       - Dynamic Side-by-Side Variant Comparison
                       - Workshop Human Review Control Buttons
```

---

## 5-Agent Sequential Handoff

The system uses a fixed 5-agent sequential prompt-chaining architecture:

1. **Detective Agent**: Builds case timeline and identifies core unanswered questions.
2. **Evidence Agent**: Evaluates every clue (FACT / INFERENCE / DISTRACTION), counts implicating vs. supporting facts, and ends with structured `SUSPECT_POSITION` lines.
3. **Suspect Agent**: Compares motive, means, opportunity, and alibis in a tabular overview.
4. **Skeptic Agent**: Challenges assumptions, planted evidence, and alternative explanations.
5. **Chief Agent**: Synthesizes validated specialist reports, states net evidence position, and recommends next steps.
6. **Human Review**: Workshop investigator reviews findings, verifies physical evidence, and selects Accept / Revise / Reject.

---

## Setup & Execution

### 1. Requirements & Prerequisites
- Python 3.10+
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Environment Configuration
Copy `.env.example` to `.env` and add your API key:
```bash
cp .env.example .env
```
Edit `.env`:
```text
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Web UI
```bash
python app.py
```
Open the local URL (`http://127.0.0.1:7860`) in your web browser.

### 5. Run Automated Tests
```bash
python -m pytest
```

---

## Key Engineering Features

- **Deterministic Python Validation (`validator.py`)**: Parses clue IDs, validates evidence references against the active case file, enforces rules against uncorroborated suspect self-statements, and computes suspect net evidence positions (`implicating_facts - supporting_facts`) directly from Evidence Agent outputs without hardcoded answer keys.
- **Python Audit Checklist Layer (`audit.py`)**: Performs post-synthesis checks on the Chief Agent verdict to ensure valid citations, bounded confidence, explicit uncertainty, alternative theories, and next investigative steps. Scores reflect structural checklist compliance, distinct from LLM confidence or statistical accuracy.
- **Evidence Lineage & Human Review (`app.py`)**: Displays leading suspect evidence lineage (implicating vs. supporting FACTs, net score, recommended band vs. stated confidence) and workshop human review control buttons (`Accept Verdict`, `Request Revision`, `Reject Verdict`).
- **Dynamic Case Variant Comparison**: Compares the original case against `CASE_FILE_VARIANT` (where Evidence E — blue velvet fibers — is removed) side-by-side with dynamic, data-driven change summaries (`WHAT CHANGED` vs `WHAT REMAINED STABLE`).
- **Rate Limit Retry Handling (`agents.py`)**: Automatic exponential backoff retry mechanism for API rate limits (HTTP 429).
- **Distinction of Scoring Systems**:
  - **LLM Stated Confidence**: Confidence percentage asserted in Chief prose.
  - **Python Recommended Band**: Deterministically bounded confidence band calculated from net evidence position.
  - **Audit Checklist Score**: Percentage of structural quality control checks passed by the Chief Agent output.
