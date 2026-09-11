import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from validator import (
    parse_evidence_classifications,
    calculate_suspect_positions,
    validate_evidence_report,
    compute_confidence_recommendation
)

def test_parse_evidence_classifications():
    report = "Clue A: FACT\nB: FACT\nC: INFERENCE\nD: FACT\nE: FACT\nF: DISTRACTION\nG: DISTRACTION\nH: DISTRACTION"
    valid_ids = ["A", "B", "C", "D", "E", "F", "G", "H"]
    classifications = parse_evidence_classifications(report, valid_ids)
    
    assert classifications["A"] == "FACT"
    assert classifications["B"] == "FACT"
    assert classifications["C"] == "INFERENCE"
    assert classifications["F"] == "DISTRACTION"

def test_suspect_evidence_counting_original():
    report = """
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
    classifications = parse_evidence_classifications(report, ["A", "B", "C", "D", "E", "F", "G", "H"])
    positions = calculate_suspect_positions(CASE_FILE, classifications, report)
    
    elena = positions["Elena Cruz"]
    assert elena["implicating_count"] == 2  # B and E
    assert elena["supporting_count"] == 0
    assert elena["net_position"] == 2
    assert elena["confidence_recommendation"]["recommended_band"] == "75% - 85%"

    julian = positions["Julian Roth"]
    assert julian["implicating_count"] == 1  # F
    assert julian["supporting_count"] == 1   # H
    assert julian["net_position"] == 0
    assert julian["confidence_recommendation"]["recommended_band"] == "30% - 50%"

    priya = positions["Priya Desai"]
    assert priya["implicating_count"] == 0
    assert priya["supporting_count"] == 1    # A
    assert priya["net_position"] == -1
    assert priya["confidence_recommendation"]["recommended_band"] == "30% - 50%"

def test_suspect_evidence_counting_variant():
    report = """
Clue A: FACT
Clue B: FACT
Clue C: INFERENCE
Clue D: FACT
Clue F: FACT

SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=A
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=D
SUSPECT_POSITION: Elena Cruz | implicating=B,E | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=F | supporting=NONE
"""
    classifications = parse_evidence_classifications(report, ["A", "B", "C", "D", "F", "G", "H"])
    positions = calculate_suspect_positions(CASE_FILE_VARIANT, classifications, report)
    
    elena = positions["Elena Cruz"]
    assert elena["implicating_count"] == 1  # B only (E is removed from valid_ids)
    assert elena["net_position"] == 1
    assert elena["confidence_recommendation"]["recommended_band"] == "55% - 65%"

def test_confidence_band_decrease_on_evidence_e_removal():
    report_orig = """
Clue B: FACT
Clue E: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B,E | supporting=NONE
"""
    report_var = """
Clue B: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B,E | supporting=NONE
"""
    class_orig = parse_evidence_classifications(report_orig, ["A", "B", "C", "D", "E", "F", "G", "H"])
    class_var = parse_evidence_classifications(report_var, ["A", "B", "C", "D", "F", "G", "H"])
    
    orig_pos = calculate_suspect_positions(CASE_FILE, class_orig, report_orig)["Elena Cruz"]
    var_pos = calculate_suspect_positions(CASE_FILE_VARIANT, class_var, report_var)["Elena Cruz"]
    
    orig_max = orig_pos["confidence_recommendation"]["recommended_max"]
    var_max = var_pos["confidence_recommendation"]["recommended_max"]
    
    assert orig_max > var_max
    assert orig_max == 85
    assert var_max == 65

def test_contested_single_evidence_capped():
    rec = compute_confidence_recommendation(net_position=1, has_physical_trace=False)
    assert rec["recommended_max"] == 65
    assert rec["recommended_band"] == "55% - 65%"

def test_validate_evidence_report_invalid_id():
    bad_report = """
Z: FACT
A: FACT
B: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B | supporting=NONE
"""
    val = validate_evidence_report(bad_report, CASE_FILE)
    assert not val["is_valid"]
    assert any("Z" in err for err in val["errors"])

def test_validate_evidence_report_variant_e_rejection():
    bad_report = """
A: FACT
B: FACT
E: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B,E | supporting=NONE
"""
    val = validate_evidence_report(bad_report, CASE_FILE_VARIANT)
    assert not val["is_valid"]
    assert any("Evidence E cited" in err for err in val["errors"])

def test_suspect_position_non_fact_warning():
    report = """
Clue B: FACT
Clue C: INFERENCE
SUSPECT_POSITION: Elena Cruz | implicating=B,C | supporting=NONE
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    elena = val["suspect_positions"]["Elena Cruz"]
    assert elena["implicating_count"] == 1
    assert "C" not in elena["implicating_clues"]
    assert any("C" in w and "Elena Cruz" in w for w in val["warnings"])

def test_suspect_position_missing_suspect_warning():
    report = """
Clue B: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B | supporting=NONE
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    marcus = val["suspect_positions"]["Marcus Webb"]
    assert marcus["implicating_count"] == 0
    assert marcus["supporting_count"] == 0
    assert any("No evidence position stated for Marcus Webb by Evidence Agent." in w for w in val["warnings"])

def test_empty_report_text_raises_error():
    with pytest.raises(ValueError, match="report_text is required"):
        calculate_suspect_positions(CASE_FILE, report_text="")
        
    val = validate_evidence_report("", CASE_FILE)
    assert not val["is_valid"]
    assert any("report_text is required" in err for err in val["errors"])

def test_unknown_suspect_name_warning():
    report = """
Clue B: FACT
SUSPECT_POSITION: Fake Person | implicating=B | supporting=NONE
SUSPECT_POSITION: Elena Cruz | implicating=B | supporting=NONE
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert "Fake Person" not in val["suspect_positions"]
    assert any("Unknown suspect 'Fake Person'" in w for w in val["warnings"])

def test_duplicate_suspect_position_warning():
    report = """
Clue B: FACT
Clue E: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B | supporting=NONE
SUSPECT_POSITION: Elena Cruz | implicating=E | supporting=NONE
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert any("Duplicate SUSPECT_POSITION line found for suspect 'Elena Cruz'" in w for w in val["warnings"])

def test_malformed_suspect_position_line_warning():
    report = """
Clue B: FACT
SUSPECT_POSITION: Elena Cruz | implicating=B
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert any("Malformed SUSPECT_POSITION line" in w for w in val["warnings"])

def test_supporting_non_fact_warning():
    report = """
Clue C: INFERENCE
SUSPECT_POSITION: Priya Desai | implicating=NONE | supporting=C
SUSPECT_POSITION: Elena Cruz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    priya = val["suspect_positions"]["Priya Desai"]
    assert priya["supporting_count"] == 0
    assert "C" not in priya["supporting_clues"]
    assert any("C" in w and "Priya Desai" in w for w in val["warnings"])

def test_critical_regression_altered_report_positions():
    # Intentionally alter positions away from Midnight Muse defaults to prove no hardcoding
    report = """
Clue B: FACT
Clue D: FACT
Clue E: FACT

SUSPECT_POSITION: Elena Cruz | implicating=B | supporting=E
SUSPECT_POSITION: Priya Desai | implicating=B,D | supporting=NONE
SUSPECT_POSITION: Marcus Webb | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Julian Roth | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    elena = val["suspect_positions"]["Elena Cruz"]
    priya = val["suspect_positions"]["Priya Desai"]

    # Elena has 1 implicating (B) and 1 supporting (E), net = 0
    assert elena["implicating_count"] == 1
    assert elena["supporting_count"] == 1
    assert elena["net_position"] == 0

    # Priya has 2 implicating (B, D) and 0 supporting, net = 2
    assert priya["implicating_count"] == 2
    assert priya["supporting_count"] == 0
    assert priya["net_position"] == 2


