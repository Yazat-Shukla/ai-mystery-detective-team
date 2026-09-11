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
    positions = calculate_suspect_positions(CASE_FILE)
    
    elena = positions["Elena Cruz"]
    assert elena["implicating_count"] == 2  # B and E
    assert elena["supporting_count"] == 0
    assert elena["net_position"] == 2
    assert elena["confidence_recommendation"]["recommended_band"] == "75% - 85%"

    julian = positions["Julian Roth"]
    assert julian["implicating_count"] == 1  # F
    assert julian["supporting_count"] == 1   # Courtyard witness alibi
    assert julian["net_position"] == 0
    assert julian["confidence_recommendation"]["recommended_band"] == "30% - 50%"

    priya = positions["Priya Desai"]
    assert priya["implicating_count"] == 0
    assert priya["supporting_count"] == 1    # Office keycard log
    assert priya["net_position"] == -1
    assert priya["confidence_recommendation"]["recommended_band"] == "30% - 50%"

def test_suspect_evidence_counting_variant():
    positions = calculate_suspect_positions(CASE_FILE_VARIANT)
    
    elena = positions["Elena Cruz"]
    assert elena["implicating_count"] == 1  # B only (E is removed)
    assert elena["net_position"] == 1
    assert elena["confidence_recommendation"]["recommended_band"] == "55% - 65%"

def test_confidence_band_decrease_on_evidence_e_removal():
    orig_pos = calculate_suspect_positions(CASE_FILE)["Elena Cruz"]
    var_pos = calculate_suspect_positions(CASE_FILE_VARIANT)["Elena Cruz"]
    
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
    bad_report = "Z: FACT\nA: FACT\nB: FACT"
    val = validate_evidence_report(bad_report, CASE_FILE)
    assert not val["is_valid"]
    assert any("Z" in err for err in val["errors"])

def test_validate_evidence_report_variant_e_rejection():
    bad_report = "A: FACT\nB: FACT\nE: FACT"
    val = validate_evidence_report(bad_report, CASE_FILE_VARIANT)
    assert not val["is_valid"]
    assert any("Evidence E cited" in err for err in val["errors"])
