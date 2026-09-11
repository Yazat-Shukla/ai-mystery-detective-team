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
