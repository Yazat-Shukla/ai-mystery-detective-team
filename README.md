# AI Mystery Detective Team

A production-quality local Python and Gradio application featuring five specialized AI agents investigating a fictional mystery case using sequential prompt handoffs, deterministic evidence validation, and automated quality control auditing.

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
                      3. Python Evidence Validator
                       - Validates Clue IDs (A-H)
                       - Classifies FACT / INFERENCE / DISTRACTION
                       - Calculates Net Evidence Positions per Suspect
                         (net = implicating_facts - exculpatory_facts)
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
                       7. Python Quality Audit Layer
                       - Validates citations & suspect references
                       - Checks alignment between net facts & confidence
                       - Verifies uncertainty & alternative theories
                                  │
                                  ▼
                         Gradio UI (2 Tabs)
                       - Workshop Markdown Reports
                       - Quality Audit & Calculated Metrics
                       - Side-by-Side Comparison & Delta Summary
                       - Human Review Notice
```

---

## 5-Agent Sequential Handoff

The system uses a fixed 5-agent sequential prompt-chaining architecture:

1. **Detective Agent**: Builds case timeline and identifies core unanswered questions.
2. **Evidence Agent**: Evaluates every clue (FACT / INFERENCE / DISTRACTION) and counts implicating vs. supporting facts.
3. **Suspect Agent**: Compares motive, means, opportunity, and alibis in a tabular overview.
4. **Skeptic Agent**: Challenges assumptions, planted evidence, and alternative explanations.
5. **Chief Agent**: Synthesizes validated specialist reports, states net evidence position, and recommends next steps.

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

- **Deterministic Python Validation (`validator.py`)**: Parses clue IDs, validates evidence references against the active case file, enforces rules against uncorroborated suspect self-statements, and computes suspect net evidence positions (`implicating_facts - supporting_facts`).
- **Quality Control Audit Layer (`audit.py`)**: Performs post-synthesis checks on the Chief Agent verdict to ensure valid citations, bounded confidence, explicit uncertainty, alternative theories, and next investigative steps.
- **Controlled Case Variant Comparison**: Compares the original case against `CASE_FILE_VARIANT` (where Evidence E — the white gesso trace — is removed) side-by-side with dynamic change summaries (`WHAT CHANGED` vs `WHAT REMAINED STABLE`).
- **Rate Limit Retry Handling (`agents.py`)**: Automatic exponential backoff retry mechanism for API rate limits (HTTP 429).
- **Human Review Principle**: Explicit human review badges reminding users that AI outputs are educational decision-support tools.
