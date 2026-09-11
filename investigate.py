import logging
from agents import AGENTS, ask_agent
from validator import validate_evidence_report, calculate_suspect_positions
from audit import audit_chief_report
from history import record_run

logger = logging.getLogger("ai_mystery_detectives")

def run_investigation(case_file: str, progress_callback=None, variant_label: str = "Original Case") -> tuple[dict[str, str], dict]:
    """
    Executes a sequential 5-agent investigation with deterministic Python validation and quality auditing.
    
    Args:
        case_file (str): Case file text.
        progress_callback (callable, optional): Progress reporting callback.
        variant_label (str): Label for the case variant (e.g. 'Original Case' or 'Variant Case').
        
    Returns:
        tuple[dict[str, str], dict]:
            - reports: Mapping of agent name to generated Markdown report.
            - metadata: Validation metrics, quality audit results, and calculated evidence positions.
    """
    reports = {}
    ordered_names = list(AGENTS.keys())
    validation_metrics = {}
    audit_results = {}
    
    logger.info(f"--- Starting investigation run: {variant_label} ---")
    
    for index, name in enumerate(ordered_names):
        if progress_callback is not None:
            progress_callback(index / len(ordered_names), desc=f'{name} is investigating...')
            
        previous = '\n\n'.join(f'## {n}\n{r}' for n, r in reports.items())
        
        # If invoking Chief Agent, append deterministic evidence calculation context
        if name == 'Chief Agent' and validation_metrics:
            positions_summary = "\n\n### DETERMINISTIC PYTHON EVIDENCE POSITIONS & CONFIDENCE BANDS:\n"
            for suspect, pos in validation_metrics.get("suspect_positions", {}).items():
                band = pos.get("confidence_recommendation", {}).get("recommended_band", "N/A")
                strength = pos.get("confidence_recommendation", {}).get("strength", "")
                positions_summary += (
                    f"- {suspect}: Net Position = {pos['net_position']} "
                    f"(Implicating FACTs: {pos['implicating_count']}, Supporting FACTs: {pos['supporting_count']}) "
                    f"-> Recommended Confidence Band: {band} [{strength}]\n"
                )
            previous += positions_summary
            
        report = ask_agent(name, AGENTS[name], case_file, previous)
        reports[name] = report
        
        # Validate Evidence Agent output after step 2
        if name == 'Evidence Agent':
            validation_metrics = validate_evidence_report(report, case_file)
            logger.info(f"Evidence validation completed. Valid: {validation_metrics['is_valid']}")
            
    # Run Quality Audit on Chief Agent's output after step 5
    if 'Chief Agent' in reports:
        audit_results = audit_chief_report(reports['Chief Agent'], case_file, validation_metrics)
        logger.info(f"Chief audit completed. Score: {audit_results['score']}/100, Passed: {audit_results['passed']}")
        
    if progress_callback is not None:
        progress_callback(1.0, desc='Case review complete')
        
    leading_suspect = audit_results.get("named_suspects", ["Unknown"])[0] if audit_results.get("named_suspects") else "Unknown"
    confidence = audit_results.get("claimed_confidence", 0) or 0
    elena_net = validation_metrics.get("suspect_positions", {}).get("Elena Cruz", {}).get("net_position", 0)
    
    record_run(
        variant_label=variant_label,
        leading_suspect=leading_suspect,
        net_position=elena_net,
        confidence=confidence,
        audit_score=audit_results.get("score", 100),
        details=audit_results
    )
    
    metadata = {
        "variant_label": variant_label,
        "validation": validation_metrics,
        "audit": audit_results,
        "suspect_positions": validation_metrics.get("suspect_positions", {})
    }
    
    return reports, metadata
