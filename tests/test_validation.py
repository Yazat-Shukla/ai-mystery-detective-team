import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from validator import (
    extract_valid_evidence_ids,
    parse_evidence_classifications,
    calculate_suspect_positions,
    validate_evidence_report,
    compute_confidence_recommendation
)

def test_parse_evidence_classifications():
    report = "Clue A: FACT\nB: FACT\nC: INFERENCE\nD: FACT\nE: FACT\nF: DISTRACTION\nG: DISTRACTION"
    valid_ids = ["A", "B", "C", "D", "E", "F", "G"]
    classifications = parse_evidence_classifications(report, valid_ids)
    
    assert classifications["A"] == "FACT"
    assert classifications["B"] == "FACT"
    assert classifications["C"] == "INFERENCE"
    assert classifications["F"] == "DISTRACTION"

def test_parse_evidence_classifications_word_boundary_regression():
    # "the case: FACT" contains "case" ending in 'e', but should NOT classify Clue E
    report = "In the case: FACT\nClue A: FACT"
    valid_ids = ["A", "B", "C", "D", "E", "F", "G"]
    classifications = parse_evidence_classifications(report, valid_ids)
    assert classifications["E"] == "UNLABELED"
    assert classifications["A"] == "FACT"

def test_suspect_evidence_counting_original():
    report = """
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
    classifications = parse_evidence_classifications(report, ["A", "B", "C", "D", "E", "F", "G"])
    positions = calculate_suspect_positions(CASE_FILE, classifications, report)
    
    arjun = positions["Arjun Vale"]
    assert arjun["implicating_count"] == 3  # B, D, E
    assert arjun["supporting_count"] == 0
    assert arjun["net_position"] == 3
    assert arjun["confidence_recommendation"]["recommended_band"] == "75% - 85%"

    lena = positions["Lena Ortiz"]
    assert lena["implicating_count"] == 0
    assert lena["supporting_count"] == 1    # F
    assert lena["net_position"] == -1
    assert lena["confidence_recommendation"]["recommended_band"] == "30% - 50%"

def test_suspect_evidence_counting_variant():
    report = """
Clue A: FACT
Clue B: FACT
Clue C: INFERENCE
Clue D: FACT
Clue F: FACT

SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=F
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Arjun Vale | implicating=B,D,E | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    classifications = parse_evidence_classifications(report, ["A", "B", "C", "D", "F", "G"])
    positions = calculate_suspect_positions(CASE_FILE_VARIANT, classifications, report)
    
    arjun = positions["Arjun Vale"]
    assert arjun["implicating_count"] == 2  # B, D only (E is removed from valid_ids)
    assert arjun["net_position"] == 2
    assert arjun["confidence_recommendation"]["recommended_band"] == "55% - 65%"

def test_confidence_band_decrease_on_evidence_e_removal():
    report_orig = """
Clue B: FACT
Clue E: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B,E | supporting=NONE
"""
    report_var = """
Clue B: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B,E | supporting=NONE
"""
    class_orig = parse_evidence_classifications(report_orig, ["A", "B", "C", "D", "E", "F", "G"])
    class_var = parse_evidence_classifications(report_var, ["A", "B", "C", "D", "F", "G"])
    
    orig_pos = calculate_suspect_positions(CASE_FILE, class_orig, report_orig)["Arjun Vale"]
    var_pos = calculate_suspect_positions(CASE_FILE_VARIANT, class_var, report_var)["Arjun Vale"]
    
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
SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=NONE
"""
    val = validate_evidence_report(bad_report, CASE_FILE)
    assert not val["is_valid"]
    assert any("Z" in err for err in val["errors"])

def test_validate_evidence_report_variant_e_rejection():
    bad_report = """
A: FACT
B: FACT
E: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B,E | supporting=NONE
"""
    val = validate_evidence_report(bad_report, CASE_FILE_VARIANT)
    assert not val["is_valid"]
    assert any("Evidence E cited" in err for err in val["errors"])

def test_suspect_position_non_fact_warning():
    report = """
Clue B: FACT
Clue C: INFERENCE
SUSPECT_POSITION: Arjun Vale | implicating=B,C | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    arjun = val["suspect_positions"]["Arjun Vale"]
    assert arjun["implicating_count"] == 1
    assert "C" not in arjun["implicating_clues"]
    assert any("C" in w and "Arjun Vale" in w for w in val["warnings"])

def test_suspect_position_missing_suspect_warning():
    report = """
Clue B: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    theo = val["suspect_positions"]["Theo Park"]
    assert theo["implicating_count"] == 0
    assert theo["supporting_count"] == 0
    assert any("No evidence position stated for Theo Park by Evidence Agent." in w for w in val["warnings"])

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
SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert "Fake Person" not in val["suspect_positions"]
    assert any("Unknown suspect 'Fake Person'" in w for w in val["warnings"])

def test_duplicate_suspect_position_warning():
    report = """
Clue B: FACT
Clue E: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=NONE
SUSPECT_POSITION: Arjun Vale | implicating=E | supporting=NONE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert any("Duplicate SUSPECT_POSITION line found for suspect 'Arjun Vale'" in w for w in val["warnings"])

def test_malformed_suspect_position_line_warning():
    report = """
Clue B: FACT
SUSPECT_POSITION: Arjun Vale | implicating=B
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    assert any("Malformed SUSPECT_POSITION line" in w for w in val["warnings"])

def test_supporting_non_fact_warning():
    report = """
Clue C: INFERENCE
SUSPECT_POSITION: Lena Ortiz | implicating=NONE | supporting=C
SUSPECT_POSITION: Arjun Vale | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    lena = val["suspect_positions"]["Lena Ortiz"]
    assert lena["supporting_count"] == 0
    assert "C" not in lena["supporting_clues"]
    assert any("C" in w and "Lena Ortiz" in w for w in val["warnings"])

def test_critical_regression_altered_report_positions():
    # Intentionally alter positions away from defaults to prove no hardcoding
    report = """
Clue B: FACT
Clue D: FACT
Clue E: FACT

SUSPECT_POSITION: Arjun Vale | implicating=B | supporting=E
SUSPECT_POSITION: Lena Ortiz | implicating=B,D | supporting=NONE
SUSPECT_POSITION: Theo Park | implicating=NONE | supporting=NONE
SUSPECT_POSITION: Sofia Reed | implicating=NONE | supporting=NONE
"""
    val = validate_evidence_report(report, CASE_FILE)
    arjun = val["suspect_positions"]["Arjun Vale"]
    lena = val["suspect_positions"]["Lena Ortiz"]

    # Arjun has 1 implicating (B) and 1 supporting (E), net = 0
    assert arjun["implicating_count"] == 1
    assert arjun["supporting_count"] == 1
    assert arjun["net_position"] == 0

    # Lena has 2 implicating (B, D) and 0 supporting, net = 2
    assert lena["implicating_count"] == 2
    assert lena["supporting_count"] == 0
    assert lena["net_position"] == 2

def test_extract_valid_evidence_ids_malformed_case_file():
    with pytest.raises(ValueError, match="Could not locate EVIDENCE section"):
        extract_valid_evidence_ids("NO EVIDENCE SECTION HERE")

def test_parse_evidence_classifications_conflicting():
    report = """
Clue B: FACT
Clue B: INFERENCE
"""
    warnings = []
    classifications = parse_evidence_classifications(report, ["B"], warnings)
    assert classifications["B"] == "CONFLICTING"
    assert any("Conflicting classifications found for Clue B" in w for w in warnings)

def test_parse_evidence_classifications_repeated_identical():
    report = """
Clue B: FACT
Clue B: FACT
"""
    warnings = []
    classifications = parse_evidence_classifications(report, ["B"], warnings)
    assert classifications["B"] == "FACT"
    assert len(warnings) == 0
