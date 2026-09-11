import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from audit import audit_chief_report, resolve_leading_suspect
from validator import calculate_suspect_positions
from history import record_run, get_run_history, clear_run_history

def test_resolve_leading_suspect_exact_and_patterns():
    # Exact pattern match
    assert resolve_leading_suspect("Most likely suspect: Arjun Vale") == "Arjun Vale"
    # Case normalization
    assert resolve_leading_suspect("Most likely suspect: arjun vale") == "Arjun Vale"
    # Whitespace normalization
    assert resolve_leading_suspect("Most likely suspect:   Arjun Vale  ") == "Arjun Vale"
    # Unmatched / near-miss name returns None (NO silent fallback)
    assert resolve_leading_suspect("Most likely suspect: John Doe") is None

def test_resolve_leading_suspect_sentence_substring_trap():
    # Sentence listing multiple suspects before giving verdict
    text = """
    Net Evidence Positions:
    - Lena Ortiz: Net -1
    - Theo Park: Net 0
    - Arjun Vale: Net +3
    - Sofia Reed: Net 0

    Conclusion and Verdict:
    Arjun Vale is the most likely suspect with 80% confidence.
    """
    assert resolve_leading_suspect(text) == "Arjun Vale"

MOCK_REPORT = """
Clue A: FACT
Clue B: FACT
Clue C: INFERENCE
Clue D: FACT
Clue E: FACT
Clue F: FACT
Clue G: DISTRACTION

SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=F
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Arjun Vale | implicating=B,D,E | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""

def test_dictionary_order_independence():
    # Reorder suspect_positions dictionary keys
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    
    # Original order
    audit1 = audit_chief_report("Most likely suspect: Arjun Vale with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit1["recommended_band"] == "75% - 85%"
    assert audit1["confidence_consistent"]
    
    # Reordered dictionary keys
    reordered_positions = {
        "Lena Ortiz": case_positions["Lena Ortiz"],
        "Sofia Reed": case_positions["Sofia Reed"],
        "Theo Park": case_positions["Theo Park"],
        "Arjun Vale": case_positions["Arjun Vale"],
    }
    audit2 = audit_chief_report("Most likely suspect: Arjun Vale with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": reordered_positions})
    assert audit2["recommended_band"] == "75% - 85%"
    assert audit2["confidence_consistent"]

def test_audit_boundary_values_inclusive():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    
    # Lower boundary: 75% for original band (75%-85%) -> Consistent
    audit_lower = audit_chief_report("Most likely suspect: Arjun Vale with 75% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit_lower["confidence_consistent"]
    
    # Upper boundary: 85% for original band (75%-85%) -> Consistent
    audit_upper = audit_chief_report("Most likely suspect: Arjun Vale with 85% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit_upper["confidence_consistent"]
    
    # Below lower boundary: 60% for original band (75%-85%) -> Mismatch / Inconsistent
    audit_mismatch = audit_chief_report("Most likely suspect: Arjun Vale with 60% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert not audit_mismatch["confidence_consistent"]
    assert audit_mismatch["recommended_band"] == "75% - 85%"

def test_audit_variant_boundary_values():
    variant_positions = calculate_suspect_positions(CASE_FILE_VARIANT, report_text=MOCK_REPORT)
    
    # Lower boundary: 55% for variant band (55%-65%) -> Consistent
    audit_lower = audit_chief_report("Most likely suspect: Arjun Vale with 55% confidence. Decisive clues: B. Remaining uncertainty exists.", CASE_FILE_VARIANT, {"suspect_positions": variant_positions})
    assert audit_lower["confidence_consistent"]
    assert audit_lower["recommended_band"] == "55% - 65%"

    # Upper boundary: 65% for variant band (55%-65%) -> Consistent
    audit_upper = audit_chief_report("Most likely suspect: Arjun Vale with 65% confidence. Decisive clues: B. Remaining uncertainty exists.", CASE_FILE_VARIANT, {"suspect_positions": variant_positions})
    assert audit_upper["confidence_consistent"]

def test_audit_idempotency():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    text = "Most likely suspect: Arjun Vale with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists."
    
    res1 = audit_chief_report(text, CASE_FILE, {"suspect_positions": case_positions})
    res2 = audit_chief_report(text, CASE_FILE, {"suspect_positions": case_positions})
    
    assert res1 == res2

def test_unmatched_suspect_no_silent_fallback():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    text = "Most likely suspect: Unknown Intruder with 80% confidence. Decisive clues: B, E."
    
    audit = audit_chief_report(text, CASE_FILE, {"suspect_positions": case_positions})
    assert not audit["checks"]["suspect_identified"]
    assert not audit["passed"]
    assert any("could not be matched" in err for err in audit["errors"])
    assert audit["recommended_band"] == "N/A"

def test_run_history_recording():
    clear_run_history()
    record_run("Original Case", "Arjun Vale", 3, 80, 100)
    record_run("Variant Case", "Lena Ortiz", 0, 45, 100)
    
    history = get_run_history()
    assert len(history) == 2
    assert history[0]["variant"] == "Original Case"
    assert history[0]["leading_suspect"] == "Arjun Vale"
    assert history[0]["net_position"] == 3
    assert history[1]["variant"] == "Variant Case"
    assert history[1]["leading_suspect"] == "Lena Ortiz"
    assert history[1]["net_position"] == 0

def test_audit_chief_citation_parsing_prose_words():
    # Prose capital letters like "I am A detective" should NOT cause invalid citation warnings
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    prose_text = "I am A lead detective writing B: FACT about Evidence B. Remaining uncertainty exists. Alternative theory considered. Recommended next step is forensic lab check."
    audit = audit_chief_report(prose_text, CASE_FILE, {"suspect_positions": case_positions})
    
    assert audit["checks"]["valid_citations"]
    assert not any("unknown letters not in case" in w for w in audit["warnings"])

def test_audit_chief_evidence_consistency_mismatch():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    # Chief claims net position +5, but actual net position for Arjun Vale is +3
    mismatch_text = "Most likely suspect: Arjun Vale with 80% confidence. Net evidence position: +5. Decisive clues: Evidence B. Remaining uncertainty exists. Alternative theory considered. Recommend interview."
    audit = audit_chief_report(mismatch_text, CASE_FILE, {"suspect_positions": case_positions})
    assert any("Chief claimed net evidence position (5) differs from deterministic calculation" in w for w in audit["warnings"])

def test_resolve_leading_suspect_cases():
    # 1. Explicit direct form
    assert resolve_leading_suspect("Arjun Vale is the most likely suspect.") == "Arjun Vale"
    
    # 2. Reverse-order multi-suspect sentence (must resolve Arjun Vale, NOT Lena Ortiz)
    assert resolve_leading_suspect("Lena Ortiz is the best alternative, while Arjun Vale is the most likely suspect.") == "Arjun Vale"
    
    # 3. Alternative mentioned after leader
    assert resolve_leading_suspect("Arjun Vale is the most likely suspect; Lena Ortiz is the best alternative.") == "Arjun Vale"
    
    # 4. Ambiguous multi-suspect line
    assert resolve_leading_suspect("Arjun Vale and Lena Ortiz are both plausible suspects.") is None
    
    # 5. Incidental mention without verdict phrase
    assert resolve_leading_suspect("Arjun Vale is discussed only as an alternative.") is None
    assert resolve_leading_suspect("Lena Ortiz is the alternative, and Arjun Vale is another possibility.") is None
    
    # 6. Negative conclusion statement (must NOT resolve suspect merely because 'Conclusion' or 'Verdict' is present)
    assert resolve_leading_suspect("Conclusion: Arjun Vale is not established as the perpetrator.") is None
    assert resolve_leading_suspect("Verdict: Arjun Vale is not established as the perpetrator.") is None
    assert resolve_leading_suspect("Verdict: Arjun Vale remains unconfirmed.") is None
    assert resolve_leading_suspect("Conclusion: Lena Ortiz is one possible explanation, but no leading suspect has been established.") is None
    
    # 7. Dictionary-order independence & case normalization
    assert resolve_leading_suspect("Most likely suspect: arjun vale") == "Arjun Vale"
    assert resolve_leading_suspect("Most likely suspect:   Arjun Vale  ") == "Arjun Vale"
    
    # 8. Unmatched / near-miss name returns None
    assert resolve_leading_suspect("Most likely suspect: John Doe") is None

def test_audit_uses_same_resolved_suspect_consistently():
    # If Lena Ortiz is resolved as leading suspect, audit must use Lena's net and confidence band
    report = """
Clue B: FACT
Clue D: FACT
SUSPECT_POSITION: Lena Ortiz | implicating=B,D | supporting=NONE
SUSPECT_POSITION: Arjun Vale | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    positions = calculate_suspect_positions(CASE_FILE, report_text=report)
    chief_text = "Most likely suspect: Lena Ortiz with 60% confidence. Decisive clues: B, D. Remaining uncertainty exists."
    audit = audit_chief_report(chief_text, CASE_FILE, {"suspect_positions": positions})
    
    assert audit["named_suspects"] == ["Lena Ortiz"]
    assert audit["recommended_band"] == "55% - 65%"
    assert audit["confidence_consistent"]

def test_sequential_isolation_original_to_variant():
    from validator import validate_evidence_report
    report_orig = """
Clue B: FACT
Clue E: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B,E | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    report_var = """
Clue B: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val_orig = validate_evidence_report(report_orig, CASE_FILE)
    val_var = validate_evidence_report(report_var, CASE_FILE_VARIANT)
    
    assert "E" in val_orig["valid_evidence_ids"]
    assert "E" not in val_var["valid_evidence_ids"]
    assert val_orig["suspect_positions"]["Arjun Vale"]["net_position"] == 2
    assert val_var["suspect_positions"]["Arjun Vale"]["net_position"] == 1
    assert val_orig["suspect_positions"]["Arjun Vale"]["confidence_recommendation"]["recommended_band"] == "75% - 85%"
    assert val_var["suspect_positions"]["Arjun Vale"]["confidence_recommendation"]["recommended_band"] == "55% - 65%"

def test_mocked_end_to_end_pipeline(monkeypatch):
    mock_responses = {
        "Detective Agent": "Timeline: Diamond disappeared between 14:00 and 14:30.",
        "Evidence Agent": """Clue B: FACT
Clue D: FACT
Clue E: FACT
SUSPECT_POSITION: Lena Ortiz | implicating=B,D | supporting=NONE
SUSPECT_POSITION: Arjun Vale | implicating=E | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE""",
        "Suspect Agent": "Lena Ortiz had opportunity. Arjun Vale had physical trace.",
        "Skeptic Agent": "Trace evidence could be secondary transfer.",
        "Chief Agent": "Most likely suspect: Lena Ortiz with 60% confidence. Net evidence position: +2. Decisive clues: B, D. Remaining uncertainty exists. Alternative theory considered. Recommend interview."
    }
    
    def mock_ask_agent(name, instruction, case_file, shared_context):
        return mock_responses[name]
        
    from investigate import run_investigation
    monkeypatch.setattr("investigate.ask_agent", mock_ask_agent)
    
    reports, meta = run_investigation(CASE_FILE, variant_label="Original Test")
    
    assert len(reports) == 5
    assert meta["leading_suspect"] == "Lena Ortiz"
    assert meta["leading_suspect_net"] == 2
    assert meta["audit"]["passed"]
    assert meta["audit"]["confidence_consistent"]

