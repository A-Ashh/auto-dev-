"""Gradio UI for Auto-SRE Interactive Sandbox Dashboard."""

import httpx
import asyncio
import os
import gradio as gr  # type: ignore

from openai import AsyncOpenAI

# The API base URL on which the app internally runs natively alongside the UI
API_BASE = os.getenv("AUTO_SRE_URL", "http://127.0.0.1:8000")
CSS = """
/* Dark Emerald / Hacker Green Theme */
.gradio-container {
    background: radial-gradient(circle at 50% 0%, #064e3b 0%, #022c22 50%, #011510 100%) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #ecfdf5 !important;
}

.card {
    padding: 16px !important;
    border-radius: 12px !important;
    background: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
}

/* Glassmorphism Panels */
.glass-panel {
    background: rgba(2, 44, 34, 0.75) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: 12px !important;
    padding: 24px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.7) !important;
}

/* Fix Input Visibility (Dropdowns, Textboxes, Numbers) */
input, select, .gr-input, .gr-box {
    background-color: #064e3b !important;
    color: #34d399 !important;
    border: 1px solid #10b981 !important;
    border-radius: 6px !important;
}
input:focus, select:focus {
    outline: none !important;
    border-color: #34d399 !important;
    box-shadow: 0 0 10px rgba(52, 211, 153, 0.4) !important;
}

/* Terminal Box */
.terminal-box textarea {
    background: #000000 !important;
    color: #10b981 !important;
    font-family: 'Fira Code', 'JetBrains Mono', monospace !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 8px !important;
    font-size: 0.95em !important;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.8) !important;
}

.terminal-input textarea {
    background: rgba(2, 44, 34, 0.9) !important;
    color: #ecfdf5 !important;
    font-family: 'Fira Code', 'JetBrains Mono', monospace !important;
    border: 1px solid rgba(16, 185, 129, 0.5) !important;
    border-radius: 8px !important;
}
.terminal-input textarea:focus {
    border-color: #34d399 !important;
    box-shadow: 0 0 15px rgba(52, 211, 153, 0.2) !important;
}

/* Buttons */
.analyze-btn {
    background: rgba(16, 185, 129, 0.15) !important;
    border: 1px solid #10b981 !important;
    color: #10b981 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}
.analyze-btn:hover {
    background: rgba(16, 185, 129, 0.3) !important;
    transform: translateY(-1px);
}

/* History / Command Log Fixes */
.history-panel {
    background: rgba(1, 21, 16, 0.8);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 8px;
    padding: 12px;
    height: 100%;
    max-height: 800px;
    overflow-y: auto;
    overflow-x: hidden;
    word-wrap: break-word;
}
.history-item {
    font-family: 'Fira Code', monospace;
    color: #a7f3d0;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(16, 185, 129, 0.1);
    padding-bottom: 8px;
    font-size: 0.85em;
}
.history-out {
    color: #10b981;
    white-space: pre-wrap;
    word-break: break-all;
    overflow-wrap: break-word;
}

/* Score and Health */
.score-display {
    font-size: 2.5em;
    font-weight: 900;
    color: #10b981;
    text-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
}

.health-good {
    color: #10b981;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(16,185,129,0.4);
}
.health-bad {
    color: #ef4444;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(239,68,68,0.4);
}
.health-wait {
    color: #f59e0b;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(245,158,11,0.4);
}
.health-neutral {
    color: #a7f3d0;
    font-weight: bold;
}

/* AI Hint Box */
.ai-hint-box {
    background: rgba(16, 185, 129, 0.1);
    border-left: 3px solid #10b981;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 12px;
    font-size: 0.9em;
    color: #d1fae5;
}
.ai-hint-title {
    font-weight: bold;
    color: #34d399;
    margin-bottom: 4px;
}
"""

FALLBACK_HINTS = {
    "t1_config": "Check /etc/app for missing or misnamed config files.",
    "t2_port": "Look for processes using port 8080 with `ps` or `netstat`.",
    "t3_dep": "Check if node_modules exist. Try running `npm install`.",
    "t4_trap": "Don't change anything yet — verify the system state first.",
    "t5_disk_full": "Check large log files in /var/log. Use `ls` or `find`.",
    "t6_oom_killer": "Look for memory-heavy processes using `ps` and kill the rogue one.",
    "t7_cascading_meltdown": "Multiple failures. Check disk, memory, and services in order.",
    "t8_memory_leak_loop": "Check RAM with free or ps. Find the rogue memory hog and kill it before restarting leak-daemon.",
    "t9_dependency_chain_failure": "Read /var/log/app.log. Ensure you restart db, then cache, then the app itself.",
    "t10_config_secret_failure": "Check /var/log/app.log to see the auth error. Echo a new secret into /etc/app/secrets.conf and restart the app."
}

TASK_DESCRIPTIONS = {
    "t1_config": "⚙️ Config file is missing or misnamed. The app cannot start. Find and restore the correct config.",
    "t2_port": "🔌 Port 8080 is occupied by a rogue process. The web server cannot bind. Identify and kill the blocker.",
    "t3_dep": "📦 Node.js dependencies are missing. The app crashes on startup. Install the required packages.",
    "t4_trap": "🪤 Trap scenario — the system may already be healthy. Investigate before taking any action.",
    "t5_disk_full": "💾 Disk is 100% full due to a massive log file in /var/log. Identify and remove it to restore service.",
    "t6_oom_killer": "🧠 A rogue process is leaking memory, triggering OOM killer. Find and terminate the memory hog.",
    "t7_cascading_meltdown": "🔥 Critical failure chain: disk is full, rogue processes exist, and services are down. System needs a full recovery.",
    "t8_memory_leak_loop": "🔄 A background process is hoarding RAM and crashing the leak-daemon. Find the memory hog, kill it, and restart the daemon.",
    "t9_dependency_chain_failure": "🔗 App is offline. Trace the logs, restart the db and cache dependencies, and then restart the app.",
    "t10_config_secret_failure": "🔒 App crashes due to authentication failure. Inspect logs, find the invalid config secret, update it, and restart the app."
}

def update_task_description(task_id: str) -> str:
    """Return HTML for the selected task's description."""
    desc = TASK_DESCRIPTIONS.get(task_id, "Select a scenario to see its description.")
    return f"<div style='background:rgba(16, 185, 129, 0.12);border-left:4px solid #10b981;border-radius:6px;padding:12px;color:#a7f3d0;font-size:0.95em;margin-top:10px;'><b>📌 Task:</b> {desc}</div>"

async def run_demo(task_id: str):
    """Auto-run the known solution commands for the selected task."""
    if not task_id:
        return "Select a task first.", "", 0.01, "<span class='health-neutral'>&#9898; NO TASK</span>", ""

    # Reset the sandbox first
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            data = resp.json()
            cwd = data.get("cwd", "/home/user")
        except Exception as e:
            return f"Demo failed during reset: {e}", "", 0.01, "<span class='health-bad'>&#128308; ERROR</span>", ""

    term_out = f"=== Demo MODE ===\nTask: {task_id}\nRunning optimal solution...\n\n"
    history_html = ""
    reward = 0.01
    done = False
    known_rogue_pid = None

    cmds = DEMO_SOLUTIONS.get(task_id, [])
    async with httpx.AsyncClient() as client:
        for cmd in cmds:
            # Substitute rogue PID placeholder once we learn it from ps output
            if "{rogue_pid}" in cmd:
                cmd = cmd.replace("{rogue_pid}", str(known_rogue_pid) if known_rogue_pid else "999")

            try:
                resp = await client.post(f"{API_BASE}/step", json={"tool": "run_command", "arguments": cmd})
                resp.raise_for_status()
                d = resp.json()

                # step API wraps stdout/stderr/cwd inside "observation"
                obs_data = d.get("observation", d)
                stdout = obs_data.get("stdout", "")
                stderr = obs_data.get("stderr", "")
                cwd = obs_data.get("cwd", cwd)
                reward = d.get("reward", reward)
                done = d.get("done", False)

                # Parse rogue PID from ps output for kill commands
                if cmd.strip().startswith("ps") and stdout and known_rogue_pid is None:
                    for line in stdout.splitlines():
                        low = line.lower()
                        if any(k in low for k in ("rogue", "leak-daemon --no-limit", "rogue-logger", "rogue-server", "memory-hog")):
                            parts = line.split()
                            for p in parts:
                                if p.isdigit() and int(p) > 1:
                                    known_rogue_pid = int(p)
                                    break

                obs = stdout or stderr or ""
                term_out += f"$ {cmd}\n{obs}\n"
                h_entry = f"<div class='history-item'><b>&gt; {cmd}</b><br><span class='history-out'>{obs}</span></div>"
                history_html = h_entry + history_html

                if done:
                    break
            except Exception as e:
                term_out += f"$ {cmd}\n[ERROR: {e}]\n"

    # Determine health from reward (consistent with api_step logic)
    if done and reward > 0.5:
        health_str = "<span class='health-good'>&#129001; HEALTHY (PASS)</span>"
    elif done:
        health_str = "<span class='health-bad'>&#10060; FAILED</span>"
    else:
        health_str = "<span class='health-wait'>&#9888; AWAITING FIX</span>"

    return term_out, cwd, reward, health_str, history_html

async def api_reset(task_id: str):
    """Call the backend reset endpoint."""
    if not task_id:
        return "Please select a scenario.", "", 0.01, "<span class='health-neutral'>&#9898; NO TASK</span>", "No task selected."
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            data = resp.json()
            cwd = data.get("cwd", "/home/user")
            return f"--- Auto-SRE Sandbox Initialized ---\nWelcome to Scenario: {task_id}\nHint: Type shell commands to diagnose and repair.\n\n$ {cwd} > ", cwd, 0.01, "<span class='health-bad'>&#10060; BROKEN</span>", "Sandbox reset."
        except Exception as e:
            return f"[API ERROR] Failed to reset: {e}", "", 0.0, "<span class='health-bad'>🔴 API ERROR</span>", "Error connecting to backend API."

async def api_step(tool: str, cmd_input: str, current_cwd: str, term_history: str, history_html: str):
    """Call the backend step endpoint and format the terminal output."""
    if not cmd_input.strip():
        return term_history, "", current_cwd, 0.0, "<span class='health-neutral'>&#9898; NO TASK</span>", history_html
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/step", json={"tool": tool, "arguments": cmd_input})
            resp.raise_for_status()
            data = resp.json()
            
            # Step endpoint returns { observation: {stdout, stderr, cwd, error}, reward, done }
            # Or if it fails at top-level: { error }
            if "error" in data and "observation" not in data:
                term_out = term_history + f"{cmd_input}\n[ERROR: {data['error']}]\n$ {current_cwd} > "
                h_entry = f"<div class='history-item'><b>> {cmd_input}</b><br><span class='history-out'>[ERROR]</span></div>"
                return term_out, "", current_cwd, 0.0, "<span class='health-bad'>🔴 API ERROR</span>", h_entry + history_html
            
            obs = data.get("observation", {})
            stdout = obs.get("stdout", "")
            stderr = obs.get("stderr", "")
            err_msg = obs.get("error", "")
            new_cwd = obs.get("cwd", current_cwd)
            
            reward = data.get("reward", 0.01)
            done = data.get("done", False)

            output_text = ""
            if stdout:
                output_text += stdout
            if stderr:
                output_text += stderr
            if err_msg:
                output_text += f"\n[Tool Error: {err_msg}]"
                
            if not output_text and not err_msg:
                output_text = ""

            term_out = term_history + f"{cmd_input}\n{output_text}\n$ {new_cwd} > "
            
            h_entry = f"<div class='history-item'><b>> {cmd_input}</b><br><span class='history-out'>{output_text}</span></div>"
            new_history_html = h_entry + history_html
            
            # Use strict reward checks corresponding to OpenEnv schema
            if done and reward > 0.5:
                health_str = "<span class='health-good'>&#129001; HEALTHY (PASS)</span>"
            elif done:
                health_str = "<span class='health-bad'>&#10060; FAILED</span>"
            else:
                health_str = "<span class='health-wait'>&#9888; AWAITING FIX</span>"
                
            return term_out, "", new_cwd, reward, health_str, new_history_html

        except Exception as e:
            term_out = term_history + f"{cmd_input}\n[HTTPX ERROR: {e}]\n$ {current_cwd} > "
            h_entry = f"<div class='history-item'><b>> {cmd_input}</b><br><span class='history-out'>[ERROR: {e}]</span></div>"
            return term_out, "", current_cwd, 0.0, "<span class='health-bad'>🔴 API ERROR</span>", h_entry + history_html


_theme = gr.themes.Base(primary_hue="emerald", neutral_hue="emerald")

with gr.Blocks(head="<style>" + CSS + "</style>", theme=_theme) as demo:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #ffffff; font-weight: 800; font-size: 2.5em; text-shadow: 0 0 20px rgba(16, 185, 129,0.8);">
            🚨 Auto-SRE Engine Terminal
        </h1>
        <p style="color: #a7f3d0; font-size: 1.1em;">Live Diagnostic & Repair Interactive Sandbox</p>
    </div>
    """)
    
    with gr.Row():
        # Left Panel (Task Control - 1x)
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["card"]):
                gr.Markdown("### 🕹️ Task Control")
                gr.Markdown("<br>")
                
                task_dropdown = gr.Dropdown(
                    choices=["t1_config", "t2_port", "t3_dep", "t4_trap", "t5_disk_full", "t6_oom_killer", "t7_cascading_meltdown", "t8_memory_leak_loop", "t9_dependency_chain_failure", "t10_config_secret_failure"],
                    label="Select Scenario",
                    value="t1_config"
                )
                task_desc_display = gr.HTML(update_task_description("t1_config"))
                
                gr.Markdown("<br>")
                reset_btn = gr.Button("🔄 Initialize Sandbox", elem_classes="analyze-btn", scale=1)
                demo_btn = gr.Button("▶ Run Demo", variant="secondary", scale=1)
                
                gr.Markdown("<br>")
                system_msg = gr.HTML("<span style='color: #6ee7b7;'>Environment not started.</span>")
                
                gr.Markdown("---")
                gr.Markdown("### 🏆 Reward Score")
                score_display = gr.Number(value=0.01, show_label=False, interactive=False, elem_classes="score-display")
                
                gr.Markdown("<br>")
                gr.Markdown("### 🏥 System Health")
                health_display = gr.HTML("<span class='health-bad'>🔴 STANDBY</span>")
                
        # Middle Panel (Terminal MAIN - 2x)
        with gr.Column(scale=2):
            with gr.Group(elem_classes=["card"]):
                gr.Markdown("### 💻 Web Terminal")
                gr.HTML("""
                <div style='background:rgba(2, 44, 34, 0.7);border:1px solid rgba(16, 185, 129, 0.25);border-radius:8px;padding:10px 16px;margin-bottom:10px;font-size:0.88em;color:#a7f3d0;'>
                    <b style='color:#10b981;'>💡 Quick Commands:</b>&nbsp;&nbsp;
                    <code>ls</code> &nbsp;·&nbsp; <code>ps</code> &nbsp;·&nbsp; <code>cat &lt;file&gt;</code> &nbsp;·&nbsp;
                    <code>kill -9 &lt;pid&gt;</code> &nbsp;·&nbsp; <code>mv &lt;src&gt; &lt;dst&gt;</code> &nbsp;·&nbsp;
                    <code>rm &lt;file&gt;</code> &nbsp;·&nbsp; <code>npm install</code>
                </div>
                """)
                
                cwd_state = gr.State("")
                
                terminal_out = gr.Textbox(
                    lines=20, 
                    max_lines=25,
                    value="[ SYSTEM OFFLINE ]\nPlease initialize a sandbox task from the control panel.", 
                    interactive=False, 
                    show_label=False, 
                    container=True,
                    elem_classes="terminal-box"
                )
                
                gr.Markdown("<br>")
                cmd_input = gr.Textbox(
                    lines=1,
                    placeholder="Type shell command (e.g. ls, ps aux, kill, mv) and press Enter...",
                    show_label=False,
                    elem_classes="terminal-input"
                )
                
                submit_btn = gr.Button("Execute Command ⚡", variant="primary", scale=1)
                
                gr.Markdown("<br>")
                copilot_btn = gr.Button("🤖 Ask AI Copilot for Hint", elem_classes="analyze-btn", scale=1)
            
        # Right Panel (History - 1x)
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["card"]):
                gr.Markdown("### 📜 Command Log")
                gr.Markdown("<br>")
                history_html = gr.HTML("", elem_classes="history-panel")

    # Event Bindings
    task_dropdown.change(
        fn=update_task_description,
        inputs=[task_dropdown],
        outputs=[task_desc_display]
    )

    reset_btn.click(
        fn=api_reset,
        inputs=[task_dropdown],
        outputs=[terminal_out, cwd_state, score_display, health_display, system_msg]
    )

    demo_btn.click(
        fn=run_demo,
        inputs=[task_dropdown],
        outputs=[terminal_out, cwd_state, score_display, health_display, history_html]
    )

    # Submitting command triggers execution and wipes input box
    submit_btn.click(
        fn=api_step,
        inputs=[gr.State("run_command"), cmd_input, cwd_state, terminal_out, history_html],
        outputs=[terminal_out, cmd_input, cwd_state, score_display, health_display, history_html]
    )
    cmd_input.submit(
        fn=api_step,
        inputs=[gr.State("run_command"), cmd_input, cwd_state, terminal_out, history_html],
        outputs=[terminal_out, cmd_input, cwd_state, score_display, health_display, history_html]
    )

    # Copilot Hint Binding
    async def get_hint(task_id: str):
        if not task_id:
            return "<div class='ai-hint-box'><div class='ai-hint-title'>Copilot says:</div>Please select a task first.</div>"
        
        # We rely on an OpenAI API call if AUTO_SRE_API_KEY is set.
        api_key = os.getenv("AUTO_SRE_API_KEY")
        if not api_key:
            # Fallback to local hardcoded hints if no API key
            hint = FALLBACK_HINTS.get(task_id, "Analyze the output and look for anomalies.")
            return f"<div class='ai-hint-box'><div class='ai-hint-title'>Copilot says (Fallback):</div>{hint}</div>"

        try:
            client = AsyncOpenAI(api_key=api_key)
            prompt = f"The user is trying to solve the SRE scenario '{task_id}'. Give them a very brief, single-sentence hint on what to look for."
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60
            )
            hint = resp.choices[0].message.content.strip()
            return f"<div class='ai-hint-box'><div class='ai-hint-title'>Copilot says:</div>{hint}</div>"
        except Exception as e:
            return f"<div class='ai-hint-box' style='border-color:#ef4444;'><div class='ai-hint-title' style='color:#ef4444;'>Copilot Error:</div>{e}</div>"

    copilot_btn.click(
        fn=get_hint,
        inputs=[task_dropdown],
        outputs=[gr.HTML()]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
