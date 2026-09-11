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

def calculate_suspect_positions(
    case_file_text: str,
    classifications: dict[str, str] = None,
    report_text: str = None,
    warnings: list = None
) -> dict[str, dict]:
    """
    Deterministically evaluates suspect evidence positions and recommended confidence bands
    strictly from report_text and classifications.
    """
    if not report_text or not report_text.strip():
        raise ValueError("report_text is required for calculate_suspect_positions and cannot be empty.")

    valid_ids = extract_valid_evidence_ids(case_file_text)
    if classifications is None:
        classifications = parse_evidence_classifications(report_text, valid_ids)

    if warnings is None:
        warnings = []

    parsed_positions = {}
    seen_suspects = set()
    duplicate_suspects = set()

    strict_pattern = r"^\s*SUSPECT_POSITION:\s*([^|]+)\|\s*implicating=([^|]*)\|\s*supporting=(.*)$"

    for line in report_text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        if "SUSPECT_POSITION" in line_clean.upper():
            match = re.match(strict_pattern, line_clean, re.IGNORECASE)
            if not match:
                warnings.append(f"Malformed SUSPECT_POSITION line: '{line_clean}'.")
                continue

            raw_name = match.group(1).strip()
            imp_raw = match.group(2).strip()
            sup_raw = match.group(3).strip()

            if not raw_name:
                warnings.append(f"Malformed SUSPECT_POSITION line (missing suspect name): '{line_clean}'.")
                continue

            matched_suspect = None
            for suspect in SUSPECT_NAMES:
                if raw_name.lower() == suspect.lower():
                    matched_suspect = suspect
                    break

            if not matched_suspect:
                warnings.append(f"Unknown suspect '{raw_name}' in Evidence Agent SUSPECT_POSITION.")
                continue

            if matched_suspect in seen_suspects:
                warnings.append(f"Duplicate SUSPECT_POSITION line found for suspect '{matched_suspect}'.")
                duplicate_suspects.add(matched_suspect)
                continue

            seen_suspects.add(matched_suspect)

            def parse_letters(raw_str):
                if raw_str.upper() == "NONE" or not raw_str:
                    return []
                return [x.strip() for x in raw_str.split(",") if x.strip()]

            parsed_positions[matched_suspect] = {
                "implicating": parse_letters(imp_raw),
                "supporting": parse_letters(sup_raw)
            }

    result = {}
    for suspect in SUSPECT_NAMES:
        if suspect not in parsed_positions or suspect in duplicate_suspects:
            if suspect not in parsed_positions:
                warnings.append(f"No evidence position stated for {suspect} by Evidence Agent.")
            conf_recommendation = compute_confidence_recommendation(
                net_position=0,
                has_physical_trace=False
            )
            result[suspect] = {
                "implicating_count": 0,
                "supporting_count": 0,
                "net_position": 0,
                "implicating_clues": [],
                "supporting_clues": [],
                "inferences": [],
                "confidence_recommendation": conf_recommendation
            }
            continue

        pos_data = parsed_positions[suspect]

        filtered_imp = []
        for letter in pos_data["implicating"]:
            if letter not in valid_ids:
                warnings.append(f"Invalid Evidence ID '{letter}' cited in SUSPECT_POSITION for {suspect}.")
            elif classifications.get(letter) != "FACT":
                warnings.append(f"Evidence letter '{letter}' cited as implicating for {suspect} was not classified as FACT.")
            else:
                filtered_imp.append(letter)

        filtered_sup = []
        for letter in pos_data["supporting"]:
            if letter not in valid_ids:
                warnings.append(f"Invalid Evidence ID '{letter}' cited in SUSPECT_POSITION for {suspect}.")
            elif classifications.get(letter) != "FACT":
                warnings.append(f"Evidence letter '{letter}' cited as supporting for {suspect} was not classified as FACT.")
            else:
                filtered_sup.append(letter)

        imp_count = len(filtered_imp)
        sup_count = len(filtered_sup)
        net = imp_count - sup_count

        has_physical_trace = ("E" in filtered_imp) and ("E" in valid_ids)

        conf_recommendation = compute_confidence_recommendation(
            net_position=net,
            has_physical_trace=has_physical_trace
        )

        result[suspect] = {
            "implicating_count": imp_count,
            "supporting_count": sup_count,
            "net_position": net,
            "implicating_clues": filtered_imp,
            "supporting_clues": filtered_sup,
            "inferences": [],
            "confidence_recommendation": conf_recommendation
        }

    return result

def validate_evidence_report(report_text: str, case_file_text: str) -> dict:
    """
    Validates Evidence Agent output and computes deterministic evidence statistics & confidence recommendations.
    """
    valid_ids = extract_valid_evidence_ids(case_file_text)

    if not report_text or not report_text.strip():
        return {
            "is_valid": False,
            "errors": ["report_text is required and cannot be empty."],
            "warnings": [],
            "valid_evidence_ids": valid_ids,
            "classifications": {},
            "suspect_positions": {}
        }

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

    try:
        suspect_positions = calculate_suspect_positions(case_file_text, classifications, report_text, warnings)
    except ValueError as ve:
        errors.append(str(ve))
        suspect_positions = {}

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "valid_evidence_ids": valid_ids,
        "classifications": classifications,
        "suspect_positions": suspect_positions
    }
