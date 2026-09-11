import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from audit import audit_chief_report, resolve_leading_suspect
from validator import calculate_suspect_positions
from history import record_run, get_run_history, clear_run_history

def test_resolve_leading_suspect_exact_and_patterns():
    # Exact pattern match
    assert resolve_leading_suspect("Most likely suspect: Elena Cruz") == "Elena Cruz"
    # Case normalization
    assert resolve_leading_suspect("Most likely suspect: elena cruz") == "Elena Cruz"
    # Whitespace normalization
    assert resolve_leading_suspect("Most likely suspect:   Elena Cruz  ") == "Elena Cruz"
    # Unmatched / near-miss name returns None (NO silent fallback)
    assert resolve_leading_suspect("Most likely suspect: John Doe") is None

def test_resolve_leading_suspect_sentence_substring_trap():
    # Sentence listing multiple suspects before giving verdict
    text = """
    Net Evidence Positions:
    - Priya Desai: Net -1
    - Marcus Webb: Net -1
    - Elena Cruz: Net +2
    - Julian Roth: Net 0

    Conclusion and Verdict:
    Elena Cruz is the most likely suspect with 80% confidence.
    """
    assert resolve_leading_suspect(text) == "Elena Cruz"

MOCK_REPORT = """
Clue A: FACT
Clue B: FACT
Clue C: INFERENCE
Clue D: FACT
Clue E: FACT
Clue F: FACT
Clue G: DISTRACTION
Clue H: FACT

SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=A
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=D
SUSPECT_POSITION: Elena Cruz | implicating=B,E | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=F | supporting=H
"""

def test_dictionary_order_independence():
    # Reorder suspect_positions dictionary keys
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    
    # Original order
    audit1 = audit_chief_report("Most likely suspect: Elena Cruz with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit1["recommended_band"] == "75% - 85%"
    assert audit1["confidence_consistent"]
    
    # Reordered dictionary keys (e.g. Priya Desai first or Julian Roth first)
    reordered_positions = {
        "Priya Desai": case_positions["Priya Desai"],
        "Julian Roth": case_positions["Julian Roth"],
        "Marcus Webb": case_positions["Marcus Webb"],
        "Elena Cruz": case_positions["Elena Cruz"],
    }
    audit2 = audit_chief_report("Most likely suspect: Elena Cruz with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": reordered_positions})
    assert audit2["recommended_band"] == "75% - 85%"
    assert audit2["confidence_consistent"]

def test_audit_boundary_values_inclusive():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    
    # Lower boundary: 75% for original band (75%-85%) -> Consistent
    audit_lower = audit_chief_report("Most likely suspect: Elena Cruz with 75% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit_lower["confidence_consistent"]
    
    # Upper boundary: 85% for original band (75%-85%) -> Consistent
    audit_upper = audit_chief_report("Most likely suspect: Elena Cruz with 85% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert audit_upper["confidence_consistent"]
    
    # Below lower boundary: 60% for original band (75%-85%) -> Mismatch / Inconsistent
    audit_mismatch = audit_chief_report("Most likely suspect: Elena Cruz with 60% confidence. Decisive clues: B, E. Remaining uncertainty exists.", CASE_FILE, {"suspect_positions": case_positions})
    assert not audit_mismatch["confidence_consistent"]
    assert audit_mismatch["recommended_band"] == "75% - 85%"  # Must NOT be 30%-50%!

def test_audit_variant_boundary_values():
    variant_positions = calculate_suspect_positions(CASE_FILE_VARIANT, report_text=MOCK_REPORT)
    
    # Lower boundary: 55% for variant band (55%-65%) -> Consistent
    audit_lower = audit_chief_report("Most likely suspect: Elena Cruz with 55% confidence. Decisive clues: B. Remaining uncertainty exists.", CASE_FILE_VARIANT, {"suspect_positions": variant_positions})
    assert audit_lower["confidence_consistent"]
    assert audit_lower["recommended_band"] == "55% - 65%"

    # Upper boundary: 65% for variant band (55%-65%) -> Consistent
    audit_upper = audit_chief_report("Most likely suspect: Elena Cruz with 65% confidence. Decisive clues: B. Remaining uncertainty exists.", CASE_FILE_VARIANT, {"suspect_positions": variant_positions})
    assert audit_upper["confidence_consistent"]

def test_audit_idempotency():
    case_positions = calculate_suspect_positions(CASE_FILE, report_text=MOCK_REPORT)
    text = "Most likely suspect: Elena Cruz with 80% confidence. Decisive clues: B, E. Remaining uncertainty exists."
    
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
    record_run("Original Case", "Elena Cruz", 2, 80, 100)
    record_run("Variant Case", "Elena Cruz", 1, 60, 100)
    
    history = get_run_history()
    assert len(history) == 2
    assert history[0]["variant"] == "Original Case"
    assert history[0]["net_position"] == 2
    assert history[1]["variant"] == "Variant Case"
    assert history[1]["net_position"] == 1
