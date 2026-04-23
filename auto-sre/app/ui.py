"""Gradio UI for Auto-SRE Interactive Sandbox Dashboard."""

import httpx
import asyncio
import os
import gradio as gr  # type: ignore

from openai import AsyncOpenAI

# The API base URL on which the app internally runs natively alongside the UI
API_BASE = "http://127.0.0.1:8000"
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
.health-wait {
    color: #fbbf24;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(251,191,36,0.5);
}
.health-neutral {
    color: #94a3b8;
    font-weight: bold;
}

/* AI Copilot Hint */
.ai-hint-box {
    background: rgba(147, 51, 234, 0.15);
    border-left: 4px solid #9333ea;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 12px;
    font-size: 0.95em;
    color: #e9d5ff;
}
.ai-hint-title {
    font-weight: bold;
    color: #c084fc;
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

DEMO_SOLUTIONS = {
    "t1_config": ["ls /etc/app", "mv /etc/app/conf.bak /etc/app/conf", "systemctl restart app"],
    "t2_port": ["ps", "kill -9 {rogue_pid}", "systemctl restart app"],
    "t3_dep": ["npm install", "systemctl restart app"],
    "t4_trap": ["ls /etc/app", "cat /etc/app/conf", "ps"],
    "t5_disk_full": ["rm /var/log/syslog"],
    "t6_oom_killer": ["ps", "kill -9 {rogue_pid}"],
    "t7_cascading_meltdown": ["df -h", "rm /var/log/syslog", "ps", "kill -9 {rogue_pid}", "systemctl restart db"],
    "t8_memory_leak_loop": ["ps", "kill -9 {rogue_pid}", "systemctl restart leak-daemon"],
    "t9_dependency_chain_failure": ["systemctl restart db", "systemctl restart cache", "systemctl restart app"],
    "t10_config_secret_failure": ["systemctl status app", "cat /var/log/app.log", "cat /etc/app/secrets.conf", "echo DB_PASSWORD=CORRECT_SECRET > /etc/app/secrets.conf", "systemctl restart app"],
}

def update_task_description(task_id: str) -> str:
    """Return HTML for the selected task's description."""
    desc = TASK_DESCRIPTIONS.get(task_id, "Select a scenario to see its description.")
    return f"<div style='background:rgba(99,102,241,0.12);border-left:4px solid #6366f1;border-radius:6px;padding:12px;color:#c7d2fe;font-size:0.95em;margin-top:10px;'><b>📌 Task:</b> {desc}</div>"

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
        health_str = "<span class='health-wait'>&#127993; AWAITING FIX</span>"

    term_out += f"\n=== Demo Complete | Reward: {reward:.3f} ==="
    return term_out, cwd, reward, health_str, history_html


async def fetch_ai_copilot_hint(task_id: str, history_html: str):
    """Securely fetch UI-only hint from LLM or fallback."""
    if not task_id:
        return history_html
    
    # Clean up history_html to raw text roughly for LLM prompt
    import re
    raw_history = re.sub(r'<[^>]+>', '\n', history_html).strip()
    if not raw_history:
        raw_history = "No commands executed yet."
        
    prompt = f"""You are a senior Site Reliability Engineer helping debug a system.

Task:
{task_id}

Recent command trace:
{raw_history[-500:]}

Give a short hint (1–2 lines).
Do NOT give the full solution.
Guide the next step."""

    hint_text = FALLBACK_HINTS.get(task_id, "Explore the system using ls, ps, and cat.")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = AsyncOpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
            resp = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=64,
                timeout=5.0
            )
            val = resp.choices[0].message.content
            if val:
                hint_text = val.strip()
    except Exception:
        pass # silently fallback
        
    # Render hint
    h_entry = f"<div class='ai-hint-box'><div class='ai-hint-title'>🤖 AI Copilot Hint</div>{hint_text}</div>"
    return h_entry + history_html

async def api_reset(task_id: str):
    """Call the backend reset API and initialize the terminal UI."""
    if not task_id:
        return "Please select a task.", "", 0.0, "<span class='health-neutral'>⚪ NO TASK</span>", "Select a task first."
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE}/reset", json={"task_id": task_id})
            resp.raise_for_status()
            data = resp.json()
            
            cwd = data.get("cwd", "/home/user")
            
            term_out = f"=== Auto-SRE Sandbox Initialized ===\nWelcome to Scenario: {task_id}\nHint: Type shell commands to diagnose and repair.\n\n$ {cwd} > "
            
            # On init the environment IS broken (that's the task) — show neutral awaiting state
            health_str = "<span class='health-wait'>🟡 AWAITING FIX</span>"
            
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
            
            # step API nests observation fields under "observation" key
            obs = data.get("observation", data)
            stdout = obs.get("stdout", "")
            stderr = obs.get("stderr", "")
            new_cwd = obs.get("cwd", current_cwd)
            # done=True AND grader returned done means the task is successfully resolved
            done = data.get("done", False)
            reward = data.get("reward", 0.01)
            # health_status in observation is True only when grader marks done=True with success
            health = done and reward > 0.5
            
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
            
            if health:
                health_str = "<span class='health-good'>🟢 HEALTHY (PASS)</span>"
            elif done and not health:
                health_str = "<span class='health-bad'>❌ FAILED / OVER</span>"
            else:
                health_str = "<span class='health-wait'>🟡 AWAITING FIX</span>"
            
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
                    choices=["t1_config", "t2_port", "t3_dep", "t4_trap", "t5_disk_full", "t6_oom_killer", "t7_cascading_meltdown", "t8_memory_leak_loop", "t9_dependency_chain_failure", "t10_config_secret_failure"],
                    label="Select Scenario",
                    value="t1_config"
                )
                task_desc_display = gr.HTML(update_task_description("t1_config"))
                reset_btn = gr.Button("🔄 Initialize Sandbox", elem_classes="analyze-btn")
                demo_btn = gr.Button("▶ Run Demo", variant="secondary")
                
                system_msg = gr.HTML("<span style='color: #94a3b8;'>Environment not started.</span>")
                
                gr.Markdown("---")
                
                gr.HTML("<h3 style='margin-bottom: 10px; margin-top:20px;'>🏆 Reward Score</h3>")
                score_display = gr.Number(value=0.01, show_label=False, interactive=False, elem_classes="score-display")
                
                gr.HTML("<h3 style='margin-bottom: 10px; margin-top:20px;'>🏥 System Health</h3>")
                health_display = gr.HTML("<span class='health-bad'>🔴 STANDBY</span>")
                
        # Middle Panel (Terminal - 50%)
        with gr.Column(scale=5):
            gr.HTML("<h3>💻 Web Terminal</h3>")
            gr.HTML("""
            <div style='background:rgba(15,23,42,0.7);border:1px solid rgba(99,102,241,0.25);border-radius:8px;padding:10px 16px;margin-bottom:10px;font-size:0.88em;color:#94a3b8;'>
                <b style='color:#a5b4fc;'>💡 Quick Commands:</b>&nbsp;&nbsp;
                <code>ls</code> &nbsp;·&nbsp; <code>ps</code> &nbsp;·&nbsp; <code>cat &lt;file&gt;</code> &nbsp;·&nbsp;
                <code>kill -9 &lt;pid&gt;</code> &nbsp;·&nbsp; <code>mv &lt;src&gt; &lt;dst&gt;</code> &nbsp;·&nbsp;
                <code>rm &lt;file&gt;</code> &nbsp;·&nbsp; <code>npm install</code>
            </div>
            """)
            
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
            
            gr.HTML("<div style='margin-top: 15px;'></div>")
            copilot_btn = gr.Button("🤖 Ask AI Copilot for Hint", elem_classes="analyze-btn")
            
        # Right Panel (History - 20%)
        with gr.Column(scale=2):
            gr.HTML("<h3>📜 Command Log</h3>")
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
    for event in [cmd_input.submit, submit_btn.click]:
        event(
            fn=api_step,
            inputs=[cmd_input, terminal_out, cwd_state, history_html],
            outputs=[terminal_out, cmd_input, cwd_state, score_display, health_display, history_html]
        )

    # Copilot button triggers independent hint fetch
    copilot_btn.click(
        fn=fetch_ai_copilot_hint,
        inputs=[task_dropdown, history_html],
        outputs=[history_html]
    )
