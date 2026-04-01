"""Gradio UI for Auto-SRE Premium Dashboard."""

import time
import random
import gradio as gr  # type: ignore

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
    animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    opacity: 0;
    transform: translateY(20px);
}

@keyframes slideUp {
    to { opacity: 1; transform: translateY(0); }
}

/* Specific Card Layouts */
.card-insight { border-left: 4px solid #a855f7; }
.card-analysis { border-left: 4px solid #3b82f6; }
.card-cause { border-left: 4px solid #f97316; }
.card-fix { border-left: 4px solid #10b981; }

.section-title {
    font-size: 0.85em;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}
.title-insight { color: #d8b4fe; }
.title-analysis { color: #93c5fd; }
.title-cause { color: #fdba74; }
.title-fix { color: #6ee7b7; }
.title-cmd { color: #c4b5fd; margin-bottom: 16px; display: block; }

/* AI Personality Header */
.ai-header {
    font-size: 1.3em;
    font-weight: 600;
    color: #e0e7ff;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    text-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
}

/* Animated Gradient Progress Bar */
.progress-bg {
    background: rgba(0, 0, 0, 0.4);
    border-radius: 99px;
    height: 12px;
    width: 100%;
    margin-right: 16px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}
.progress-fill {
    background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
    height: 100%;
    border-radius: 99px;
    width: 0%; /* Animates to final width */
    transition: width 1.5s cubic-bezier(0.22, 1, 0.36, 1);
    box-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
}

/* Severity Badges */
.badge {
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 0.9em;
    letter-spacing: 1px;
    display: inline-block;
}
.badge-high {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid #ef4444;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
}
.badge-med {
    background: rgba(234, 179, 8, 0.15);
    color: #fef08a;
    border: 1px solid #eab308;
    box-shadow: 0 0 15px rgba(234, 179, 8, 0.3);
}

/* Command Blocks */
.cmd-block {
    position: relative;
    background: #0f172a;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid rgba(99, 102, 241, 0.3);
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
}
.cmd-code {
    font-family: 'Fira Code', monospace;
    color: #34d399;
    font-size: 0.95em;
    overflow-x: auto;
}
.copy-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.5);
    color: #e0e7ff;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8em;
    font-weight: bold;
    transition: all 0.2s;
    white-space: nowrap;
}
.copy-btn:hover {
    background: rgba(99, 102, 241, 0.4);
    box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
}

/* Inputs & Buttons Glows */
#issue-box textarea {
    background: rgba(0, 0, 0, 0.3) !important;
    border: 2px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    color: #f8fafc !important;
    font-size: 1.1em !important;
    transition: all 0.3s ease !important;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.5) !important;
}
#issue-box textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 25px rgba(99, 102, 241, 0.3), inset 0 0 15px rgba(99, 102, 241, 0.2) !important;
    outline: none !important;
}

.analyze-btn {
    background: linear-gradient(135deg, #4f46e5, #9333ea) !important;
    border: none !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 1.15em !important;
    border-radius: 12px !important;
    padding: 14px 0 !important;
    margin-top: 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 20px rgba(147, 51, 234, 0.5) !important;
}
.analyze-btn:hover {
    box-shadow: 0 0 30px rgba(147, 51, 234, 0.8) !important;
    transform: translateY(-2px);
}

.suggestion-btn {
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    color: #cbd5e1 !important;
    transition: all 0.2s !important;
}
.suggestion-btn:hover {
    background: rgba(99, 102, 241, 0.2) !important;
    border-color: #818cf8 !important;
    color: #ffffff !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.3) !important;
}

/* Thinking Loader Animation */
.loader-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 24px;
}
.loader-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(99, 102, 241, 0.2);
    border-top-color: #818cf8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    box-shadow: 0 0 20px rgba(129, 140, 248, 0.5);
}
@keyframes spin { 100% { transform: rotate(360deg); } }
.loader-text {
    font-size: 1.4em;
    font-weight: 600;
    color: #e0e7ff;
    text-shadow: 0 0 10px rgba(129, 140, 248, 0.6);
    letter-spacing: 1px;
}
"""

def generate_commands_html(cmds_str: str) -> str:
    """Wrap each command in its own styled block with a copy button."""
    blocks = []
    for cmd in cmds_str.strip().split('\n'):
        if not cmd.strip(): continue
        # Escape quotes for JS inline
        escaped_cmd = cmd.replace("'", "\\'").replace('"', '&quot;')
        block = f"""
        <div class="cmd-block">
            <code class="cmd-code">{cmd}</code>
            <button class="copy-btn" onclick="navigator.clipboard.writeText('{escaped_cmd}'); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000)">Copy</button>
        </div>
        """
        blocks.append(block)
    return "\n".join(blocks)


def simulate_analysis(issue: str):
    if not issue.strip():
        yield "<div class='glass-panel'><h3 style='color:#fca5a5;'>⚠️ Please describe an issue to begin.</h3></div>"
        return

    # Animated AI Thinking Phases with 1.5s delay
    phases = [
        "📡 Analyzing telemetry...",
        "🔍 Detecting anomaly...",
        "⚙️ Generating fix plan..."
    ]

    for phase in phases:
        yield f"""
        <div class="loader-container">
            <div class="loader-spinner"></div>
            <div class="loader-text">{phase}</div>
        </div>
        """
        time.sleep(1.6)

    # Output Formulation
    issue_lower = issue.lower()
    conf = random.randint(88, 98)

    if "cpu" in issue_lower:
        insight = "Critical CPU saturation detected on vSphere-Node-3. System telemetry indicates a rogue phantom process is bypassing namespace constraints."
        analysis = "Identified abnormal resource utilization on `worker-node-3`. The telemetry graph shows a sustained 99.8% CPU bound constraint aligning perfectly with the latest auto-scaling event."
        rc = "Rogue phantom process loop in the data ingestion worker."
        sev = "<div class='badge badge-high'>[ 🔴 HIGH RISK ]</div>"
        fix = "1. Isolate worker-node-3 from load balancer\n2. Locate and kill the rogue process\n3. Patch CPU cgroup limits via DaemonSet config"
        cmds = "kubectl cordon worker-node-3\nkill -9 $(pgrep phantom.sh)"
    elif "500" in issue_lower or "api" in issue_lower:
        insight = "Immediate database exhaustion identified. The API gateway is failing to route requests because the backend `auth-service` connection pool is entirely occupied."
        analysis = "Traced ingress routes revealing high latencies and direct 500 error cascades terminating at PostgreSQL."
        rc = "Database connection pool exhausted due to unclosed sessions in the auth layer."
        sev = "<div class='badge badge-high'>[ 🔴 HIGH RISK ]</div>"
        fix = "1. Scale up PgBouncer replicas\n2. Restart auth-service pods immediately\n3. Rollback recent authentication PR #492"
        cmds = "kubectl rollout restart deploy/auth-api\npsql -c 'SELECT pg_terminate_backend(pid...)'"
    else:
        insight = "Deployment lifecycle interrupted. Kubelet logs confirm the container runtime is instantly crashing upon starting the main entrypoint."
        analysis = "Analyzed kubelet event streams and container exit codes (137/1). Found immediate boot failure loops associated with missing runtime binaries."
        rc = "Missing Node.js package dependencies causing application boot crash loops."
        sev = "<div class='badge badge-med'>[ 🟡 MEDIUM ]</div>"
        fix = "1. Re-run npm install in build directory to restore node_modules\n2. Verify package-lock.json hashes against registry\n3. Restart application daemon"
        cmds = "cd /home/user/app && npm install\npm2 restart all"
         
    cmd_html = generate_commands_html(cmds)

    yield f"""
    <!-- Final Premium Output Structure -->
    
    <div class="ai-header">
        🤖 Auto-SRE Insight: <span style="font-weight: 400; color: #a5b4fc; font-style: italic;">{insight}</span>
    </div>

    <div style='display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; margin-bottom: 20px;'>
        <!-- Severity Card -->
        <div class="output-card" style="margin-bottom: 0; display:flex; flex-direction:column; justify-content:center; align-items:flex-start; animation-delay: 0.1s;">
            <div class="section-title" style="color:#94a3b8;">System Severity</div>
            {sev}
        </div>
        
        <!-- Confidence Card -->
        <div class="output-card card-insight" style="margin-bottom: 0; display:flex; flex-direction:column; justify-content:center; animation-delay: 0.2s;">
            <div class="section-title title-insight" style="display:flex; justify-content:space-between;">
                <span>AI Confidence Score</span>
                <span style="font-size: 1.4em; color: #fff;">{conf}%</span>
            </div>
            <div class="progress-bg">
                <!-- Trigger width transition smoothly initialized from 0 to target % via HTML injection -->
                <div class="progress-fill" style="width: {conf}%;"></div>
            </div>
        </div>
    </div>

    <!-- Analysis -->
    <div class="output-card card-analysis" style="animation-delay: 0.3s;">
        <div class="section-title title-analysis">🔍 Analysis</div>
        <div style="font-size:1.1em; line-height:1.6; color:#e2e8f0;">{analysis}</div>
    </div>
    
    <!-- Root Cause -->
    <div class="output-card card-cause" style="animation-delay: 0.4s;">
        <div class="section-title title-cause">⚠️ Root Cause</div>
        <div style="font-size:1.1em; line-height:1.6; color:#fed7aa;">{rc}</div>
    </div>

    <!-- Fix Plan -->
    <div class="output-card card-fix" style="animation-delay: 0.5s;">
        <div class="section-title title-fix">✅ Fix Plan</div>
        <pre style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 8px; color: #a7f3d0; margin:0; border: 1px solid rgba(16,185,129,0.2); font-family: system-ui; font-size: 1.05em; line-height:1.6;">{fix}</pre>
    </div>
    
    <!-- Commands -->
    <div style="margin-top: 24px; animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; animation-delay: 0.6s;">
        <span class="section-title title-cmd">⚙️ Executable Commands</span>
        {cmd_html}
    </div>
    """


_theme = gr.themes.Base(primary_hue="indigo", neutral_hue="slate")

with gr.Blocks(css=CSS, theme=_theme) as demo:
    with gr.Row(equal_height=True):
        
        # Left Panel (40%)
        with gr.Column(scale=4):
            with gr.Column(elem_classes="glass-panel"):
                gr.HTML("""
                <h1 style="color: #ffffff; font-weight: 800; font-size: 2em; letter-spacing: -0.5px; text-shadow: 0 0 20px rgba(99,102,241,0.6); margin-bottom: 24px;">
                    🧠 Describe Incident
                </h1>
                """)
                
                issue_input = gr.Textbox(lines=7, label="", placeholder="Paste logs, describe metrics, or report anomalies here...", elem_id="issue-box", show_label=False)
                
                gr.HTML("<div style='margin-top: 24px; margin-bottom: 12px; font-size: 0.85em; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;'>Quick Diagnostics</div>")
                
                with gr.Row():
                    btn1 = gr.Button("CPU spike", elem_classes="suggestion-btn", size="sm")
                    btn2 = gr.Button("API 500 error", elem_classes="suggestion-btn", size="sm")
                    btn3 = gr.Button("Container crash", elem_classes="suggestion-btn", size="sm")
                    
                analyze_btn = gr.Button("🚀 Trigger AI Diagnostics", elem_classes="analyze-btn")
                
                btn1.click(lambda: "Urgent: I'm seeing a massive CPU spike on worker node 3. Things are slowing down to a crawl.", None, issue_input)
                btn2.click(lambda: "Alert: Increased API 500 errors from the billing service endpoint observed over the last 15 minutes.", None, issue_input)
                btn3.click(lambda: "Deploy failed: The Node.js container keeps crashing continuously upon boot.", None, issue_input)
            
        # Right Panel (60%)
        with gr.Column(scale=6):
            output_html = gr.HTML("""
            <div style='display:flex; height:100%; min-height:600px; align-items:center; justify-content:center; border: 2px dashed rgba(99,102,241,0.3); border-radius: 16px; background: rgba(0,0,0,0.2);'>
                <h3 style='color:#64748b; font-family: "Fira Code", monospace; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0,0,0,0.5);'>[ WAITING FOR TELEMETRY INPUT ]</h3>
            </div>
            """)
            
    analyze_btn.click(fn=simulate_analysis, inputs=issue_input, outputs=output_html)
