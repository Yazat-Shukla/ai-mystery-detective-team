import re

SUSPECT_NAMES = [
    "Priya Desai",
    "Marcus Webb",
    "Elena Cruz",
    "Julian Roth"
]

def extract_valid_evidence_ids(case_file_text: str) -> list[str]:
    """
    Extracts all evidence letters (e.g. ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])
    present in the CASE FILE text.
    """
    evidence_section = re.search(r"EVIDENCE\s*\n(.*?)(?:\n\n|\nUNRESOLVED|\nRULES|$)", case_file_text, re.DOTALL)
    if not evidence_section:
        return ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    matches = re.findall(r"^([A-Z])\.\s+", evidence_section.group(1), re.MULTILINE)
    return sorted(list(set(matches)))

def parse_evidence_classifications(report_text: str, valid_ids: list[str]) -> dict[str, str]:
    """
    Parses clue classifications from Evidence Agent report text.
    Looks for patterns like 'A: FACT', 'B: FACT', 'C: INFERENCE', 'E: FACT', etc.
    """
    classifications = {}
    for letter in valid_ids:
        pattern = r"(?:Clue\s+)?\[?" + letter + r"\]?[\s:\-]+(FACT|INFERENCE|DISTRACTION)"
        match = re.search(pattern, report_text, re.IGNORECASE)
        if match:
            classifications[letter] = match.group(1).upper()
        else:
            classifications[letter] = "UNLABELED"
    return classifications

def compute_confidence_recommendation(net_position: int, has_physical_trace: bool) -> dict:
    """
    Deterministically computes a recommended confidence band based on net evidence position
    and physical trace corroboration.
    """
    if net_position >= 2 and has_physical_trace:
        return {
            "recommended_band": "75% - 85%",
            "recommended_min": 75,
            "recommended_max": 85,
            "strength": "Very Strong (Access Log + Corroborated Physical Trace Evidence)"
        }
    elif net_position >= 1:
        return {
            "recommended_band": "55% - 65%",
            "recommended_min": 55,
            "recommended_max": 65,
            "strength": "Moderate / Capped (Access Log only, Physical Trace absent)"
        }
    else:
        return {
            "recommended_band": "30% - 50%",
            "recommended_min": 30,
            "recommended_max": 50,
            "strength": "Low / Uncorroborated / Contested"
        }

def calculate_suspect_positions(case_file_text: str, classifications: dict[str, str] = None) -> dict[str, dict]:
    """
    Deterministically evaluates suspect evidence positions and recommended confidence bands.
    """
    valid_ids = extract_valid_evidence_ids(case_file_text)
    has_gesso = "E" in valid_ids
    
    positions = {
        "Priya Desai": {
            "implicating_facts": [],
            "supporting_facts": ["Office Keycard Log (7:40-8:05 PM)"],
            "inferences": ["Claims she was finalizing auction paperwork"],
            "contradictions": ["Insurance payout goes to parent trust, not individual"]
        },
        "Marcus Webb": {
            "implicating_facts": [],
            "supporting_facts": ["Lobby Camera Footage (7:40-7:55 PM)"],
            "inferences": ["East Wing camera offline for maintenance"],
            "contradictions": []
        },
        "Elena Cruz": {
            "implicating_facts": ["B: East Wing door access log at 7:47 PM"],
            "supporting_facts": [],
            "inferences": ["C: Statement that badge was left on lab coat in workshop"],
            "contradictions": []
        },
        "Julian Roth": {
            "implicating_facts": ["F: Rejected pre-auction offer"],
            "supporting_facts": ["Courtyard alibi confirmed by two guests (7:42-7:53 PM)"],
            "inferences": [],
            "contradictions": ["Two independent guests confirm courtyard presence"]
        }
    }
    
    if has_gesso:
        positions["Elena Cruz"]["implicating_facts"].append("E: Restoration gesso trace on East Wing doorframe")
        
    result = {}
    for suspect, data in positions.items():
        imp_count = len(data["implicating_facts"])
        sup_count = len(data["supporting_facts"])
        net = imp_count - sup_count
        conf_recommendation = compute_confidence_recommendation(
            net_position=net,
            has_physical_trace=(suspect == "Elena Cruz" and has_gesso)
        )
        result[suspect] = {
            "implicating_count": imp_count,
            "supporting_count": sup_count,
            "net_position": net,
            "implicating_clues": data["implicating_facts"],
            "supporting_clues": data["supporting_facts"],
            "inferences": data["inferences"],
            "confidence_recommendation": conf_recommendation
        }
        
    return result

def validate_evidence_report(report_text: str, case_file_text: str) -> dict:
    """
    Validates Evidence Agent output and computes deterministic evidence statistics & confidence recommendations.
    """
    valid_ids = extract_valid_evidence_ids(case_file_text)
    classifications = parse_evidence_classifications(report_text, valid_ids)
    
    errors = []
    warnings = []
    
    all_cited_letters = re.findall(r"\b([A-Z])\s*[\:\-]\s*(?:FACT|INFERENCE|DISTRACTION)\b", report_text)
    for letter in set(all_cited_letters):
        if letter not in valid_ids:
            errors.append(f"Invalid Evidence ID '{letter}' cited. Case file only contains: {', '.join(valid_ids)}")
            
    if "E" not in valid_ids and re.search(r"\bE\b", report_text):
        errors.append("Evidence E cited, but Evidence E is removed from this case variant!")
        
    if "C" in classifications and classifications["C"] == "FACT":
        warnings.append("Clue C (Elena's statement) was labeled as FACT. Suspect self-statements should be INFERENCE unless corroborated.")
        
    suspect_positions = calculate_suspect_positions(case_file_text, classifications)
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "valid_evidence_ids": valid_ids,
        "classifications": classifications,
        "suspect_positions": suspect_positions
    }
