import pytest
from case_file import CASE_FILE, CASE_FILE_VARIANT
from validator import extract_valid_evidence_ids

def test_case_file_content():
    assert "The Missing Midnight Muse" in CASE_FILE
    assert "Priya Desai" in CASE_FILE
    assert "Marcus Webb" in CASE_FILE
    assert "Elena Cruz" in CASE_FILE
    assert "Julian Roth" in CASE_FILE

def test_case_file_variant_difference():
    assert CASE_FILE != CASE_FILE_VARIANT
    assert "E. Trace evidence" in CASE_FILE
    assert "E. Trace evidence" not in CASE_FILE_VARIANT

def test_extract_valid_evidence_ids():
    orig_ids = extract_valid_evidence_ids(CASE_FILE)
    var_ids = extract_valid_evidence_ids(CASE_FILE_VARIANT)
    
    assert orig_ids == ["A", "B", "C", "D", "E", "F", "G", "H"]
    assert var_ids == ["A", "B", "C", "D", "F", "G", "H"]
    assert "E" not in var_ids
