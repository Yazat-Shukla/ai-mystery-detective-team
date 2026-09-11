import os
import time
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ai_mystery_detectives")

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing. Please set it in your .env file or environment.")

client = genai.Client(api_key=API_KEY)
MODEL = 'gemini-3.5-flash-lite'

AGENTS = {
    'Detective Agent': '''Build a concise case timeline. Identify the central mystery and the three most important unanswered questions. Do not decide guilt yet.''',
    'Evidence Agent': '''Evaluate every clue for reliability and relevance. Label each clue FACT, INFERENCE, or DISTRACTION, citing its letter (e.g. 'B: FACT'). Treat a suspect's own uncorroborated statement about their own actions or whereabouts as INFERENCE, never FACT, unless independently corroborated by another source (camera, witness, or log from someone else). For each suspect, separately count FACT-labeled clues that directly implicate them versus FACT-labeled clues that support their alibi or exclude them. Identify the strongest evidence and explain why, citing evidence letters explicitly.

End your report with one line per suspect, in this exact machine-parseable format:
SUSPECT_POSITION: <Full Suspect Name> | implicating=<comma-separated evidence letters or NONE> | supporting=<comma-separated evidence letters or NONE>
where "implicating" lists FACT-labeled clues that directly point to that suspect, and "supporting" lists FACT-labeled clues that support their alibi or exclude them. Example line:
SUSPECT_POSITION: Arjun Vale | implicating=B,E | supporting=NONE''',
    'Suspect Agent': '''Compare every suspect's motive, means, opportunity, and alibi. Use a compact table. Rank suspects, but explicitly state what is not proven.''',
    'Skeptic Agent': '''Challenge the current investigation. Find alternative explanations, weak assumptions, possible planted evidence, and missing information. State what would change the conclusion.''',
    'Chief Agent': '''Act as the responsible investigation chief. Synthesize the specialist reports. Before naming a suspect, state their net evidence position: FACT-labeled clues that implicate them, minus FACT-labeled clues that support their alibi or exclude them, citing letters for each. Name the most likely suspect and give a confidence percentage derived from that net count — more net implicating facts with fewer contradictions should mean higher confidence; a single uncorroborated or contested fact should not exceed 60%. Cite the decisive clues by letter, discuss the best alternative theory, and recommend the next investigative step. Never claim certainty beyond the evidence.''',
}

def ask_agent(name, instruction, case_file, shared_context, max_retries=3):
    """
    Invokes the Gemini model for a given agent role with retry handling for rate limits (429).
    """
    prompt = f'''You are the {name} in a multi-agent detective team.

YOUR ROLE
{instruction}

CASE FILE
{case_file}

REPORTS FROM EARLIER AGENTS
{shared_context or 'None—you are the first agent.'}

Return a clear workshop-friendly report under 250 words. Use only supplied information.'''

    logger.info(f"Invoking {name} using model {MODEL}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt)
            logger.info(f"{name} completed successfully.")
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
                sleep_time = attempt * 5
                logger.warning(f"Rate limit hit for {name} on attempt {attempt}/{max_retries}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"API call error for {name}: {err_str}")
                raise e

    raise RuntimeError(f"Failed to execute {name} after {max_retries} attempts due to API rate limits.")
