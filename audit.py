import re
from validator import extract_valid_evidence_ids, SUSPECT_NAMES

def resolve_leading_suspect(chief_report: str) -> str | None:
    """
    Extracts and resolves the primary/leading suspect named by the Chief Agent.
    Requires explicit semantic association or unambiguous single-suspect verdict context.
    Prevents arbitrary occurrence order or dictionary fallbacks when multiple suspects appear in prose.
    """
    if not chief_report:
        return None

    # 1. Look for explicit verdict/leading suspect pattern
    patterns = [
        r"(?:most likely suspect|leading suspect|primary suspect|prime suspect|named suspect)[\s:\-\*]+(?:is\s+)?\*?\*?([A-Z][a-z]+\s+[A-Z][a-z]+)\*?\*?",
        r"\*?\*?([A-Z][a-z]+\s+[A-Z][a-z]+)\*?\*?\s+(?:is|remains|identified as)\s+(?:the\s+)?(?:most likely|leading|primary|prime)\s+(?:suspect|perpetrator)",
        r"\bverdict[\s:\-\*]+\*?\*?([A-Z][a-z]+\s+[A-Z][a-z]+)\*?\*?(?:$|[\.\,\;\n])"
    ]
    for pattern in patterns:
        match = re.search(pattern, chief_report, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            for suspect in SUSPECT_NAMES:
                if candidate.lower() == suspect.lower():
                    return suspect

    # 2. Search lines containing explicit positive verdict key phrases (unambiguous single-suspect context)
    negs = ["not", "never", "unproven", "unconfirmed", "doubt", "alternative"]
    for line in chief_report.splitlines():
        line_lower = line.lower()
        if any(re.search(r"\b" + neg + r"\b", line_lower) for neg in negs):
            continue
        if any(kw in line_lower for kw in ["most likely suspect", "leading suspect", "primary suspect", "prime suspect"]):
            found_suspects = [s for s in SUSPECT_NAMES if s.lower() in line_lower]
            if len(found_suspects) == 1:
                return found_suspects[0]

    return None

def audit_chief_report(chief_report: str, case_file_text: str, validation_metrics: dict) -> dict:
    """
    Performs a deterministic Python quality control audit on the Chief Agent's verdict.
    Evaluates structural completeness, citation validity, and consistency against deterministic metrics.
    Note: The audit score is a structural checklist score, not an AI model accuracy percentage.
    """
    valid_ids = extract_valid_evidence_ids(case_file_text)
    suspect_positions = validation_metrics.get("suspect_positions", {})
    checks = {}
    warnings = []
    errors = []
    
    # 1. Named Suspect Resolution
    leading_suspect = resolve_leading_suspect(chief_report)
    checks["suspect_identified"] = leading_suspect is not None
    
    if leading_suspect:
        named_suspects = [leading_suspect]
    else:
        named_suspects = []
        errors.append("Chief suspect could not be matched to deterministic suspect data")
        
    # 2. Cited Evidence Validity Check (uses explicit citation patterns to avoid false positives on prose capitals)
    citation_patterns = [
        r"\b(?:Evidence|Clue|Letter)\s+([A-Z])\b",
        r"\bclues?\s+([A-Z])\b",
        r"\[([A-Z])\]",
        r"\(([A-Z])\)",
        r"\b([A-Z])\s*[\:\-]\s*(?:FACT|INFERENCE|DISTRACTION)\b"
    ]
    found_citations = set()
    for pattern in citation_patterns:
        for match in re.finditer(pattern, chief_report, re.IGNORECASE):
            found_citations.add(match.group(1).upper())

    invalid_citations = [c for c in found_citations if c not in valid_ids]
    
    checks["valid_citations"] = len(invalid_citations) == 0
    if invalid_citations:
        warnings.append(f"Chief report cited unknown letters not in case: {', '.join(sorted(invalid_citations))}")
        
    if "E" not in valid_ids and "E" in found_citations:
        errors.append("Chief report cited Evidence E, but Evidence E is removed from this case variant!")
        
    # 3. Uncertainty Check
    checks["uncertainty_acknowledged"] = any(
        w in chief_report.lower() for w in ["uncertain", "unconfirmed", "not proven", "possibility", "doubt", "uncertainty"]
    )
    if not checks["uncertainty_acknowledged"]:
        warnings.append("Chief report failed to explicitly acknowledge remaining uncertainty.")
        
    # 4. Alternative Theory Check
    checks["alternative_theory_included"] = any(
        w in chief_report.lower() for w in ["alternative", "theory", "other suspect", "planted", "borrowed"]
    )
    if not checks["alternative_theory_included"]:
        warnings.append("Chief report missing explicit discussion of alternative theories.")
        
    # 5. Next Investigative Step Check
    checks["next_step_recommended"] = any(
        w in chief_report.lower() for w in ["next step", "recommend", "investigate", "interview", "forensic", "verify"]
    )
    if not checks["next_step_recommended"]:
        warnings.append("Chief report missing recommended next investigative step.")
        
    # 6. Bounded & Deterministic Confidence Alignment Check
    conf_match = re.search(r"(\d{1,3})\s*%", chief_report)
    claimed_confidence = int(conf_match.group(1)) if conf_match else None
    
    if leading_suspect and leading_suspect in suspect_positions:
        suspect_meta = suspect_positions[leading_suspect]
        conf_rec = suspect_meta.get("confidence_recommendation", {})
        recommended_min = conf_rec.get("recommended_min", 30)
        recommended_max = conf_rec.get("recommended_max", 85)
        recommended_band = conf_rec.get("recommended_band", "55% - 85%")
        
        confidence_consistent = True
        if claimed_confidence is not None:
            # Inclusive comparison: lower <= claimed <= upper
            if not (recommended_min <= claimed_confidence <= recommended_max):
                confidence_consistent = False
                warnings.append(
                    f"WARNING: Chief confidence ({claimed_confidence}%) differs from deterministic evidence assessment "
                    f"(recommended band: {recommended_band})."
                )

        # Net evidence position consistency check
        net_match = re.search(r"net(?:\s+evidence)?\s+(?:position|count)[\s:\-=]+\+?(-?\d+)", chief_report, re.IGNORECASE)
        if net_match:
            claimed_net = int(net_match.group(1))
            actual_net = suspect_meta.get("net_position")
            if actual_net is not None and claimed_net != actual_net:
                warnings.append(
                    f"WARNING: Chief claimed net evidence position ({claimed_net}) differs from deterministic calculation "
                    f"({actual_net}) for {leading_suspect}."
                )
    else:
        confidence_consistent = False
        recommended_band = "N/A"
        if leading_suspect is None:
            warnings.append("WARNING: Chief confidence could not be validated against deterministic band (unresolved suspect name).")
            
    checks["confidence_consistent"] = confidence_consistent
    
    passed_count = sum(1 for v in checks.values() if v)
    checklist_score = int((passed_count / len(checks)) * 100) if checks else 100
    
    return {
        "passed": len(errors) == 0,
        "score": checklist_score,  # Python Audit Checklist Score
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "named_suspects": named_suspects,
        "claimed_confidence": claimed_confidence,
        "recommended_band": recommended_band,
        "confidence_consistent": confidence_consistent,
        "human_review_required": True
    }
