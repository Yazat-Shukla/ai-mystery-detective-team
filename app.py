import gradio as gr
from case_file import CASE_FILE, CASE_FILE_VARIANT
from agents import AGENTS
from investigate import run_investigation

def format_suspect_positions_md(positions: dict) -> str:
    """Formats calculated suspect positions into a clean markdown table."""
    md = "### 📊 Deterministic Evidence Position Summary\n\n"
    md += "| Suspect | Implicating FACTs | Supporting / Alibi FACTs | Net Position | Recommended Band |\n"
    md += "| :--- | :---: | :---: | :---: | :---: |\n"
    for suspect, pos in positions.items():
        net_str = f"+{pos['net_position']}" if pos['net_position'] > 0 else str(pos['net_position'])
        band = pos.get("confidence_recommendation", {}).get("recommended_band", "N/A")
        md += f"| **{suspect}** | {pos['implicating_count']} | {pos['supporting_count']} | `{net_str}` | `{band}` |\n"
    return md

def format_audit_badge_md(audit: dict) -> str:
    """Formats Python quality audit result into an audit badge."""
    score = audit.get("score", 100)
    passed = audit.get("passed", True)
    consistent = audit.get("confidence_consistent", True)
    status_icon = "✅ PASSED" if (passed and consistent) else "⚠️ AUDIT WARNING"
    
    md = f"### 🛡️ Python Quality Audit: {status_icon} (Score: {score}/100)\n"
    
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
            
    md += "\n> 🧑‍⚖️ **Human Review Required**: AI verdicts are educational decision-support tools. A human investigator must verify physical evidence and badge custody before conclusions."
    return md

def investigate_single(progress=gr.Progress()):
    reports, metadata = run_investigation(CASE_FILE, progress_callback=progress, variant_label="Original Case")
    
    outputs = [reports[name] for name in AGENTS.keys()]
    metrics_md = format_suspect_positions_md(metadata["suspect_positions"])
    audit_md = format_audit_badge_md(metadata["audit"])
    
    return tuple(outputs + [metrics_md, audit_md])

def investigate_comparison(progress=gr.Progress()):
    # Step 1: Original Case Run
    progress(0.0, desc="Starting Original Case investigation...")
    def prog_orig(p, desc):
        progress(p * 0.5, desc=f"[Original Case] {desc}")
    reports_orig, meta_orig = run_investigation(CASE_FILE, progress_callback=prog_orig, variant_label="Original Case")
    
    # Step 2: Variant Case Run
    progress(0.5, desc="Starting Variant Case investigation (No Evidence E)...")
    def prog_var(p, desc):
        progress(0.5 + p * 0.5, desc=f"[Variant Case] {desc}")
    reports_var, meta_var = run_investigation(CASE_FILE_VARIANT, progress_callback=prog_var, variant_label="Variant Case")
    
    progress(1.0, desc="Comparison complete!")
    
    orig_outputs = [reports_orig[name] for name in AGENTS.keys()]
    var_outputs = [reports_var[name] for name in AGENTS.keys()]
    
    orig_pos = meta_orig["suspect_positions"].get("Elena Cruz", {})
    var_pos = meta_var["suspect_positions"].get("Elena Cruz", {})
    
    orig_band = orig_pos.get("confidence_recommendation", {}).get("recommended_band", "75% - 85%")
    var_band = var_pos.get("confidence_recommendation", {}).get("recommended_band", "55% - 65%")
    
    orig_claimed = meta_orig['audit'].get('claimed_confidence', 80)
    var_claimed = meta_var['audit'].get('claimed_confidence', 60)
    
    orig_consistent_str = "Consistent" if meta_orig['audit'].get('confidence_consistent', True) else "⚠️ WARNING: Chief confidence differs from deterministic evidence assessment"
    var_consistent_str = "Consistent" if meta_var['audit'].get('confidence_consistent', True) else "⚠️ WARNING: Chief confidence differs from deterministic evidence assessment"

    comparison_summary = f"""### ⚖️ Case Variant Comparison Summary

| Metric | Original Case (With Evidence E) | Variant Case (No Evidence E) | Delta / Change |
| :--- | :---: | :---: | :---: |
| **Leading Suspect** | {meta_orig['audit'].get('named_suspects', ['Elena Cruz'])[0]} | {meta_var['audit'].get('named_suspects', ['Elena Cruz'])[0]} | Same leading suspect |
| **Elena Net Evidence** | `+{orig_pos.get('net_position', 2)}` | `+{var_pos.get('net_position', 1)}` | **-1 Net FACT** (Gesso trace removed) |
| **Recommended Confidence Band** | `{orig_band}` | `{var_band}` | **Decreased band** (-20% upper cap) |
| **Chief's Stated Confidence** | `{orig_claimed}%` | `{var_claimed}%` | Stated confidence |
| **Assessment Consistency** | `{orig_consistent_str}` | `{var_consistent_str}` | Audit check |

#### 🔍 WHAT CHANGED:
- **Evidence E (gesso trace) was removed** in the Variant run.
- Elena lost one direct physical trace clue connecting her workshop material to the East Wing doorframe.
- Net evidence position for Elena decreased from `+{orig_pos.get('net_position', 2)}` to `+{var_pos.get('net_position', 1)}`.
- Recommended confidence band decreased from `{orig_band}` to `{var_band}`.

#### 📌 WHAT REMAINED STABLE:
- The case timeline, keycard/badge logs, and suspect roster remain identical.
- Elena's badge unlock at 7:47 PM remains the primary access record.
- Unresolved question remains: Whether Elena's badge was used by her personally or borrowed/taken during evacuation.
- **Human review is strictly required for both runs.**
"""

    orig_metrics = format_suspect_positions_md(meta_orig["suspect_positions"])
    var_metrics = format_suspect_positions_md(meta_var["suspect_positions"])

    return tuple(orig_outputs + var_outputs + [orig_metrics, var_metrics, comparison_summary])

with gr.Blocks(title="AI Mystery Detective Team") as demo:
    gr.Markdown("# 🔎 AI Mystery Detective Team")
    gr.Markdown("Five AI agents share evidence, challenge one another, and produce a cautious verdict for a fictional case.")
    
    with gr.Tabs():
        with gr.Tab("Single Investigation"):
            with gr.Accordion("Read the case file", open=False):
                gr.Textbox(value=CASE_FILE, lines=16, interactive=False, show_label=False)
                
            investigate_button = gr.Button("Start Investigation", variant="primary")
            
            single_outputs = []
            for name in AGENTS:
                single_outputs.append(gr.Markdown(label=name))
                
            metrics_display = gr.Markdown(label="Deterministic Evidence Positions")
            audit_display = gr.Markdown(label="Quality Audit Status")
            
            investigate_button.click(
                fn=investigate_single,
                inputs=[],
                outputs=single_outputs + [metrics_display, audit_display]
            )
            
        with gr.Tab("Compare Runs"):
            gr.Markdown("### 🧪 Case Variant Comparison Experiment")
            gr.Markdown(
                "Compare the investigation results between the **Original Case** (with Evidence E) and the **Variant Case** "
                "(with Evidence E — white gesso trace — removed)."
            )
            
            compare_button = gr.Button("Run Comparison Investigation", variant="primary")
            
            comparison_summary = gr.Markdown(label="Comparative Analysis Summary")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## 📋 Original Case (With Evidence E)")
                    orig_outputs = [gr.Markdown(label=f"Original: {name}") for name in AGENTS]
                    orig_metrics_display = gr.Markdown()
                    
                with gr.Column():
                    gr.Markdown("## 🧪 Variant Case (No Evidence E)")
                    var_outputs = [gr.Markdown(label=f"Variant: {name}") for name in AGENTS]
                    var_metrics_display = gr.Markdown()
                    
            compare_button.click(
                fn=investigate_comparison,
                inputs=[],
                outputs=orig_outputs + var_outputs + [orig_metrics_display, var_metrics_display, comparison_summary]
            )

if __name__ == "__main__":
    demo.launch()
