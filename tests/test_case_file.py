import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from validator import extract_valid_evidence_ids

def test_case_file_content():
    assert "The Vanishing Aurora Diamond" in CASE_FILE
    assert "Lena Ortiz" in CASE_FILE
    assert "Theo Park" in CASE_FILE
    assert "Arjun Vale" in CASE_FILE
    assert "Sofia Reed" in CASE_FILE

def test_case_file_variant_difference():
    assert CASE_FILE != CASE_FILE_VARIANT
    assert "E. Blue velvet fibers" in CASE_FILE
    assert "E. Blue velvet fibers" not in CASE_FILE_VARIANT

def test_extract_valid_evidence_ids():
    orig_ids = extract_valid_evidence_ids(CASE_FILE)
    var_ids = extract_valid_evidence_ids(CASE_FILE_VARIANT)
    
    assert orig_ids == ["A", "B", "C", "D", "E", "F", "G"]
    assert var_ids == ["A", "B", "C", "D", "F", "G"]
    assert "E" not in var_ids
