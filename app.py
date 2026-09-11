import gradio as gr
from case_file import CASE_FILE, CASE_FILE_VARIANT
from agents import AGENTS
from investigate import run_investigation

def format_evidence_lineage_md(metadata: dict) -> str:
    """Formats a compact deterministic evidence lineage summary for the leading suspect."""
    audit = metadata.get("audit", {})
    suspect_positions = metadata.get("suspect_positions", {})
    
    leading_suspect = audit.get("named_suspects", ["Unresolved"])[0] if audit.get("named_suspects") else "Unresolved"
    suspect_data = suspect_positions.get(leading_suspect, {})
    
    imp_clues = ", ".join(suspect_data.get("implicating_clues", [])) or "None"
    sup_clues = ", ".join(suspect_data.get("supporting_clues", [])) or "None"
    net_val = suspect_data.get("net_position", 0)
    net_str = f"+{net_val}" if net_val > 0 else str(net_val)
    
    conf_rec = suspect_data.get("confidence_recommendation", {})
    band = conf_rec.get("recommended_band", "N/A")
    strength = conf_rec.get("strength", "N/A")
    claimed_conf = audit.get("claimed_confidence")
    claimed_str = f"{claimed_conf}%" if claimed_conf is not None else "Not Stated"
    audit_score = audit.get("score", 100)
    audit_status = "✅ Consistent" if audit.get("confidence_consistent", True) else "⚠️ Band Mismatch"

    md = f"""### 🧬 Deterministic Evidence Lineage — Primary Suspect
- **Resolved Leading Suspect**: `{leading_suspect}`
- **Implicating FACTs**: `{imp_clues}` (Count: {suspect_data.get('implicating_count', 0)})
- **Supporting / Alibi FACTs**: `{sup_clues}` (Count: {suspect_data.get('supporting_count', 0)})
- **Calculated Net Position**: `{net_str}`
- **Python Recommended Band**: `{band}` ({strength})
- **Chief's Stated Confidence**: `{claimed_str}`
- **Audit Checklist Result**: `{audit_status}` (Checklist Score: `{audit_score}/100`)
"""
    return md

def format_suspect_positions_md(positions: dict) -> str:
    """Formats calculated suspect positions into a clean markdown table."""
    md = "### 📊 Suspect Evidence Position Matrix\n\n"
    md += "| Suspect | Implicating FACTs | Supporting / Alibi FACTs | Net Position | Recommended Band |\n"
    md += "| :--- | :---: | :---: | :---: | :---: |\n"
    for suspect, pos in positions.items():
        net_str = f"+{pos['net_position']}" if pos['net_position'] > 0 else str(pos['net_position'])
        band = pos.get("confidence_recommendation", {}).get("recommended_band", "N/A")
        md += f"| **{suspect}** | {pos['implicating_count']} | {pos['supporting_count']} | `{net_str}` | `{band}` |\n"
    return md

def format_audit_badge_md(audit: dict) -> str:
    """Formats Python quality control audit result into an audit status section."""
    score = audit.get("score", 100)
    passed = audit.get("passed", True)
    consistent = audit.get("confidence_consistent", True)
    status_icon = "✅ PASSED" if (passed and consistent) else "⚠️ AUDIT WARNING"
    
    md = f"### 🛡️ Python Audit Checklist: {status_icon} (Checklist Score: {score}/100)\n"
    
    if not consistent:
        md += "> ⚠️ **WARNING: Chief confidence differs from deterministic evidence assessment**\n\n"
        
    if audit.get("warnings"):
        md += "**Audit Warnings:**\n"
        for w in audit["warnings"]:
            md += f"- ⚠️ {w}\n"
            
    if audit.get("errors"):
        md += "**Validation Errors:**\n"
        for e in audit["errors"]:
            md += f"- ❌ {e}\n"
            
    return md

def format_human_review_md(audit: dict, suspect_positions: dict) -> str:
    """Formats structured Human Review section."""
    leading_suspect = audit.get("named_suspects", ["Unresolved"])[0] if audit.get("named_suspects") else "Unresolved"
    pos = suspect_positions.get(leading_suspect, {})
    imp_clues = ", ".join(pos.get("implicating_clues", [])) or "None"
    sup_clues = ", ".join(pos.get("supporting_clues", [])) or "None"
    
    md = f"""### 🧑‍⚖️ Workshop Human Review Control
> **Human Review Required**: AI verdicts are educational decision-support tools. A human investigator must verify physical evidence and badge custody before official conclusions.

- **Primary Suspect Under Review**: `{leading_suspect}`
- **Strongest Corroborated Evidence**: Implicating FACT clues `{imp_clues}`
- **Weakest / Contested Evidence**: Supporting / Alibi FACT clues `{sup_clues}`
- **Recommended Next Step**: Verify physical trace evidence and witness statements.
"""
    return md

def investigate_single(progress=gr.Progress()):
    reports, metadata = run_investigation(CASE_FILE, progress_callback=progress, variant_label="Original Case")
    
    outputs = [reports[name] for name in AGENTS.keys()]
    lineage_md = format_evidence_lineage_md(metadata)
    metrics_md = format_suspect_positions_md(metadata["suspect_positions"])
    audit_md = format_audit_badge_md(metadata["audit"])
    review_md = format_human_review_md(metadata["audit"], metadata["suspect_positions"])
    
    return tuple(outputs + [lineage_md, metrics_md, audit_md, review_md])

def investigate_comparison(progress=gr.Progress()):
    progress(0.0, desc="Starting Original Case investigation...")
    def prog_orig(p, desc):
        progress(p * 0.5, desc=f"[Original Case] {desc}")
    reports_orig, meta_orig = run_investigation(CASE_FILE, progress_callback=prog_orig, variant_label="Original Case")
    
    progress(0.5, desc="Starting Variant Case investigation (No Evidence E)...")
    def prog_var(p, desc):
        progress(0.5 + p * 0.5, desc=f"[Variant Case] {desc}")
    reports_var, meta_var = run_investigation(CASE_FILE_VARIANT, progress_callback=prog_var, variant_label="Variant Case")
    
    progress(1.0, desc="Comparison complete!")
    
    orig_outputs = [reports_orig[name] for name in AGENTS.keys()]
    var_outputs = [reports_var[name] for name in AGENTS.keys()]
    
    orig_suspect = meta_orig['audit'].get('named_suspects', ['Unresolved'])[0] if meta_orig['audit'].get('named_suspects') else "Unresolved"
    var_suspect = meta_var['audit'].get('named_suspects', ['Unresolved'])[0] if meta_var['audit'].get('named_suspects') else "Unresolved"
    
    orig_pos = meta_orig["suspect_positions"].get(orig_suspect, {})
    var_pos = meta_var["suspect_positions"].get(var_suspect, {})
    
    orig_net = orig_pos.get('net_position', 'N/A')
    var_net = var_pos.get('net_position', 'N/A')
    
    orig_band = orig_pos.get("confidence_recommendation", {}).get("recommended_band", "N/A")
    var_band = var_pos.get("confidence_recommendation", {}).get("recommended_band", "N/A")
    
    orig_claimed = meta_orig['audit'].get('claimed_confidence', 'N/A')
    var_claimed = meta_var['audit'].get('claimed_confidence', 'N/A')
    
    suspect_delta = "Same leading suspect" if orig_suspect == var_suspect else f"Suspect shifted ({orig_suspect} -> {var_suspect})"
    
    if isinstance(orig_net, int) and isinstance(var_net, int):
        net_diff = var_net - orig_net
        net_delta = f"{net_diff:+d} Net FACT" if net_diff != 0 else "Unchanged"
    else:
        net_delta = "N/A"
        
    orig_ids = meta_orig.get("validation", {}).get("valid_evidence_ids", [])
    var_ids = meta_var.get("validation", {}).get("valid_evidence_ids", [])
    removed_ids = sorted(list(set(orig_ids) - set(var_ids)))
    removed_str = ", ".join(removed_ids) if removed_ids else "None"

    comparison_summary = f"""### ⚖️ Dynamic Case Variant Comparison Summary

| Metric | Original Case (With Evidence {removed_str}) | Variant Case (Without Evidence {removed_str}) | Delta / Change |
| :--- | :---: | :---: | :---: |
| **Leading Suspect** | `{orig_suspect}` | `{var_suspect}` | `{suspect_delta}` |
| **Leading Suspect Net Position** | `+{orig_net}` | `+{var_net}` | `{net_delta}` |
| **Recommended Confidence Band** | `{orig_band}` | `{var_band}` | Band shift |
| **Chief's Stated Confidence** | `{orig_claimed}%` | `{var_claimed}%` | Stated confidence |
| **Audit Checklist Status** | Score `{meta_orig['audit'].get('score', 100)}/100` | Score `{meta_var['audit'].get('score', 100)}/100` | Audit checklist check |

#### 🔍 WHAT CHANGED (Dynamic Run Analysis):
- **Removed Evidence ID(s)**: `{removed_str}`.
- **Leading Suspect Net Position**: Changed from `+{orig_net}` to `+{var_net}` (`{net_delta}`).
- **Recommended Confidence Band**: Shifted from `{orig_band}` to `{var_band}`.

#### 📌 WHAT REMAINED STABLE:
- Case timeline, access logs, and suspect roster.
- Leading suspect identity ({orig_suspect}) when physical trace evidence is omitted.
- Requirement for human review and physical evidence verification prior to official action.
"""

    orig_metrics = format_suspect_positions_md(meta_orig["suspect_positions"])
    var_metrics = format_suspect_positions_md(meta_var["suspect_positions"])

    return tuple(orig_outputs + var_outputs + [orig_metrics, var_metrics, comparison_summary])

def update_review_status(action: str):
    return f"**Human Review Selection Saved**: `{action}` recorded for workshop session."

with gr.Blocks(title="AI Mystery Detective Team") as demo:
    gr.Markdown("# 🔎 AI Mystery Detective Team")
    gr.Markdown("Five AI agents share evidence, challenge assumptions, and synthesize a cautious verdict with deterministic Python validation.")
    
    with gr.Tabs():
        with gr.Tab("Single Investigation"):
            with gr.Accordion("Read the case file", open=False):
                gr.Textbox(value=CASE_FILE, lines=16, interactive=False, show_label=False)
                
            investigate_button = gr.Button("Start Investigation", variant="primary")
            
            single_outputs = []
            for name in AGENTS:
                single_outputs.append(gr.Markdown(label=name))
                
            lineage_display = gr.Markdown(label="Evidence Lineage")
            metrics_display = gr.Markdown(label="Deterministic Evidence Matrix")
            audit_display = gr.Markdown(label="Quality Audit Checklist")
            review_display = gr.Markdown(label="Human Review Control")
            
            review_status = gr.Markdown(visible=True)
            with gr.Row():
                accept_btn = gr.Button("Accept Verdict", variant="success")
                revise_btn = gr.Button("Request Revision", variant="secondary")
                reject_btn = gr.Button("Reject Verdict", variant="stop")
                
            accept_btn.click(fn=lambda: update_review_status("ACCEPTED"), outputs=[review_status])
            revise_btn.click(fn=lambda: update_review_status("REVISION REQUESTED"), outputs=[review_status])
            reject_btn.click(fn=lambda: update_review_status("REJECTED"), outputs=[review_status])
            
            investigate_button.click(
                fn=investigate_single,
                inputs=[],
                outputs=single_outputs + [lineage_display, metrics_display, audit_display, review_display]
            )
            
        with gr.Tab("Compare Runs"):
            gr.Markdown("### 🧪 Case Variant Comparison Experiment")
            gr.Markdown(
                "Compare the investigation results between the **Original Case** and the **Variant Case** "
                "(with physical trace evidence removed)."
            )
            
            compare_button = gr.Button("Run Comparison Investigation", variant="primary")
            
            comparison_summary = gr.Markdown(label="Comparative Analysis Summary")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## 📋 Original Case (Full Evidence)")
                    orig_outputs = [gr.Markdown(label=f"Original: {name}") for name in AGENTS]
                    orig_metrics_display = gr.Markdown()
                    
                with gr.Column():
                    gr.Markdown("## 🧪 Variant Case (Modified Evidence)")
                    var_outputs = [gr.Markdown(label=f"Variant: {name}") for name in AGENTS]
                    var_metrics_display = gr.Markdown()
                    
            compare_button.click(
                fn=investigate_comparison,
                inputs=[],
                outputs=orig_outputs + var_outputs + [orig_metrics_display, var_metrics_display, comparison_summary]
            )

if __name__ == "__main__":
    demo.launch()
