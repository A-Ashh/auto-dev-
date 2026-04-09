"""Gradio UI for Auto-SRE Interactive Sandbox Dashboard."""

import httpx
import asyncio
import gradio as gr  # type: ignore

# The API base URL on which the app internally runs natively alongside the UI
API_BASE = "http://127.0.0.1:7860"

CSS = """
.gradio-container {
    background: radial-gradient(circle at 50% 0%, #311bb6 0%, #0f172a 50%, #020617 100%) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #f8fafc !important;
}

/* Glassmorphism Panels */
.glass-panel {
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 16px !important;
    padding: 30px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(99, 102, 241, 0.05) !important;
}

/* Output Cards */
.output-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.terminal-box textarea {
    background: #000000 !important;
    color: #34d399 !important;
    font-family: 'Fira Code', monospace !important;
    border: 1px solid rgba(52, 211, 153, 0.3) !important;
    border-radius: 8px !important;
}

.terminal-input textarea {
    background: #1e293b !important;
    color: #f8fafc !important;
    font-family: 'Fira Code', monospace !important;
    border: 2px solid rgba(99, 102, 241, 0.5) !important;
    border-radius: 8px !important;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5) !important;
}
.terminal-input textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.4) !important;
}

.analyze-btn {
    background: linear-gradient(135deg, #4f46e5, #9333ea) !important;
    border: none !important;
    color: white !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
    box-shadow: 0 0 15px rgba(147, 51, 234, 0.4) !important;
    transition: all 0.3s ease !important;
}
.analyze-btn:hover {
    box-shadow: 0 0 25px rgba(147, 51, 234, 0.7) !important;
    transform: translateY(-2px);
}

.history-panel {
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 8px;
    padding: 16px;
    height: 100%;
}
.history-item {
    font-family: monospace;
    color: #a5b4fc;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
}
.history-out {
    color: #94a3b8;
    font-size: 0.9em;
    white-space: pre-wrap;
}

.score-display {
    font-size: 2.5em;
    font-weight: 900;
    color: #34d399;
    text-shadow: 0 0 20px rgba(52, 211, 153, 0.5);
}

.health-good {
    color: #34d399;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(52,211,153,0.5);
}
.health-bad {
    color: #ef4444;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(239,68,68,0.5);
}
"""

async def api_reset(task_id: str):
    """Call the backend reset API and initialize the terminal UI."""
    if not task_id:
        return "Please select a task.", "", 0.0, "<span class='health-bad'>🔴 BROKEN</span>", "Select a task first."
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            data = resp.json()
            
            cwd = data.get("cwd", "/home/user")
            health = data.get("health_status", False)
            
            term_out = f"=== Auto-SRE Sandbox Initialized ===\nWelcome to Scenario: {task_id}\nHint: Type shell commands to diagnose and repair.\n\n$ {cwd} > "
            
            health_str = "<span class='health-good'>🟢 HEALTHY</span>" if health else "<span class='health-bad'>🔴 BROKEN</span>"
            
            return term_out, cwd, 0.01, health_str, "Environment Reset: " + task_id
            
        except Exception as e:
            term_out = f"Error connecting to backend API: {e}\nIs the backend running at {API_BASE}?"
            return term_out, "", 0.0, "<span class='health-bad'>🔴 API ERROR</span>", ""

async def api_step(cmd_input: str, term_history: str, current_cwd: str, history_html: str):
    """Call the backend step API with the latest shell command and update scoreboard."""
    if not current_cwd:
        return term_history, "", term_history, 0.0, "<span class='health-bad'>🔴 START TASK FIRST</span>", history_html
        
    if not cmd_input.strip():
        # Empty command handling
        term_out = term_history + "\n$ " + current_cwd + " > "
        return term_out, "", current_cwd, gr.update(), gr.update(), history_html

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/step", json={
                "tool": "run_command", "arguments": cmd_input
            })
            resp.raise_for_status()
            data = resp.json()
            
            stdout = data.get("stdout", "")
            stderr = data.get("stderr", "")
            new_cwd = data.get("cwd", current_cwd)
            health = data.get("health_status", False)
            reward = data.get("reward", 0.01)
            done = data.get("done", False)
            
            # Combine formatting
            cmd_echo = f"{cmd_input}\n"
            obs_out = ""
            if stdout:
                obs_out += stdout
                if not stdout.endswith("\\n"): obs_out += "\\n"
            if stderr:
                obs_out += f"STDERR: {stderr}"
                if not stderr.endswith("\\n"): obs_out += "\\n"
                
            term_out = term_history + cmd_echo + obs_out + f"$ {new_cwd} > "
            
            # Formulate the updated History Log display
            h_entry = f"<div class='history-item'><b>> {cmd_input}</b><br><span class='history-out'>{obs_out}</span></div>"
            new_history_html = h_entry + history_html
            
            health_str = "<span class='health-good'>🟢 HEALTHY (PASS)</span>" if health else "<span class='health-bad'>🔴 BROKEN</span>"
            if done and not health:
                health_str = "<span class='health-bad'>❌ FAILED / OVER</span>"
            
            return term_out, "", new_cwd, reward, health_str, new_history_html
            
        except Exception as e:
            term_out = term_history + f"{cmd_input}\n[HTTPX ERROR: {e}]\n$ {current_cwd} > "
            h_entry = f"<div class='history-item'><b>> {cmd_input}</b><br><span class='history-out'>[ERROR: {e}]</span></div>"
            return term_out, "", current_cwd, 0.0, "<span class='health-bad'>🔴 API ERROR</span>", h_entry + history_html


_theme = gr.themes.Base(primary_hue="indigo", neutral_hue="slate")

with gr.Blocks(head="<style>" + CSS + "</style>", theme=_theme) as demo:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #ffffff; font-weight: 800; font-size: 2.5em; text-shadow: 0 0 20px rgba(99,102,241,0.6);">
            🚨 Auto-SRE Engine Terminal
        </h1>
        <p style="color: #94a3b8; font-size: 1.1em;">Live Diagnostic & Repair Interactive Sandbox</p>
    </div>
    """)
    
    with gr.Row(equal_height=True):
        # Left Panel (Scoreboard & Controls - 30%)
        with gr.Column(scale=3):
            with gr.Column(elem_classes="glass-panel"):
                gr.HTML("<h3 style='margin-bottom: 20px;'>🕹️ Task Control</h3>")
                
                task_dropdown = gr.Dropdown(
                    choices=["t1_config", "t2_port", "t3_dep", "t4_trap"],
                    label="Select Scenario",
                    value="t1_config"
                )
                reset_btn = gr.Button("🔄 Initialize Sandbox", elem_classes="analyze-btn")
                
                system_msg = gr.HTML("<span style='color: #94a3b8;'>Environment not started.</span>")
                
                gr.Markdown("---")
                
                gr.HTML("<h3 style='margin-bottom: 10px; margin-top:20px;'>🏆 Reward Score</h3>")
                score_display = gr.Number(value=0.01, show_label=False, interactive=False, elem_classes="score-display")
                
                gr.HTML("<h3 style='margin-bottom: 10px; margin-top:20px;'>🏥 System Health</h3>")
                health_display = gr.HTML("<span class='health-bad'>🔴 STANDBY</span>")
                
        # Middle Panel (Terminal - 50%)
        with gr.Column(scale=5):
            gr.HTML("<h3>💻 Web Terminal</h3>")
            
            cwd_state = gr.State("")
            
            terminal_out = gr.Textbox(
                lines=15, 
                value="[ SYSTEM OFFLINE ]\nPlease initialize a sandbox task from the control panel.", 
                interactive=False, 
                show_label=False, 
                elem_classes="terminal-box"
            )
            
            cmd_input = gr.Textbox(
                lines=1,
                placeholder="Type shell command (e.g. ls, ps aux, kill, mv) and press Enter...",
                show_label=False,
                elem_classes="terminal-input"
            )
            
            submit_btn = gr.Button("Execute Command ⚡", variant="primary")
            
        # Right Panel (History - 20%)
        with gr.Column(scale=2):
            gr.HTML("<h3>📜 Command Log</h3>")
            history_html = gr.HTML("", elem_classes="history-panel")

    # Event Bindings
    reset_btn.click(
        fn=api_reset,
        inputs=[task_dropdown],
        outputs=[terminal_out, cwd_state, score_display, health_display, system_msg]
    )
    
    # Submitting command triggers execution and wipes input box
    for event in [cmd_input.submit, submit_btn.click]:
        event(
            fn=api_step,
            inputs=[cmd_input, terminal_out, cwd_state, history_html],
            outputs=[terminal_out, cmd_input, cwd_state, score_display, health_display, history_html]
        )
