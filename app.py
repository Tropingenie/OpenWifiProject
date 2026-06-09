import queue
import logging
import logging.handlers
import time
import threading
import subprocess
import gradio as gr

from main import main, LOG_LEVEL, IFNAME_2
from shared import nmcli_lock

# =====================================================================
# 1. LOGGING & QUEUE SETUP
# =====================================================================

log_queue = queue.Queue()

# Use a unified logger name so everything routes to our custom handler
logger = logging.getLogger("gradio app")
logger.setLevel(LOG_LEVEL)

queue_handler = logging.handlers.QueueHandler(log_queue)
logger.addHandler(queue_handler)
logging.getLogger("main").addHandler(queue_handler)

console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(console_formatter)
logger.addHandler(stream_handler)


# =====================================================================
# 2. BACKGROUND SCRIPT SIMULATION (Uses native logger)
# =====================================================================

threading.Thread(target=main, daemon=True).start()


# =====================================================================
# 3. INTERFACE LOGIC
# =====================================================================

def get_internet_status():
    try:
        subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "🟢 Online"
    except subprocess.CalledProcessError:
        return "🔴 Offline"

log_history = []

def update_dashboard():
    global log_history

    while not log_queue.empty():
        try:
            record = log_queue.get_nowait()
            # Wrap lines in HTML spans with coloring based on severity level
            color = "white"
            if record.levelno >= logging.ERROR:
                color = "#ff6b6b"  # Light Red
            elif record.levelno >= logging.WARNING:
                color = "#fcc419"  # Light Yellow
            
            formatted_line = f"<span style='color: {color};'>[{time.strftime('%H:%M:%S', time.localtime(record.created))}] {record.getMessage()}</span>"
            log_history.append(formatted_line)
        except queue.Empty:
            break
            
    # Keep the last 50 lines in history so you can see past errors, but height is constrained by CSS
    visible_logs = "<br>".join(log_history[-50:])
    return visible_logs, get_internet_status()

def connect_to_network(ssid, password):
    global nmcli_lock
    logger.info(f"Manual connection request submitted for SSID: {ssid}")
    
    with nmcli_lock:
        logger.info(f"Connecting to SSID: {ssid}")
        returned_process = subprocess.run(f"nmcli dev wifi connect '{ssid}' password {password} ifname {IFNAME_2}", shell=True, capture_output=True, text=True)
    
    # FIX: Changed from generic 'logging.info' to 'logger.info' so it hits your queue handler!
    if len(returned_process.stdout) > 0:
        logger.info(returned_process.stdout.strip())
    if len(returned_process.stderr) > 0:
        logger.error(returned_process.stderr.strip())
        
    if returned_process.returncode != 0:
        return f"❌ Failed to connect to network: '{ssid}'. {returned_process.stderr.strip()}"
    return f"✅ Successfully sent request to connect to network: '{ssid}'"


# =====================================================================
# 4. CUSTOM CSS FOR THE FAKE TERMINAL (Handles Auto-Scroll & Fixed Height)
# =====================================================================

# This CSS styles our HTML box like a terminal and forces the scrollbar to stay pinned to the bottom.
custom_css = """
.terminal-box {
    background-color: #1e1e1e;
    color: #f1f1f1;
    font-family: 'Courier New', Courier, monospace;
    padding: 12px;
    border-radius: 6px;
    height: 320px;
    overflow-y: auto;
    font-size: 13px;
    line-height: 1.5;
    border: 1px solid #333;
    display: flex;
    flex-direction: column-reverse; /* Clever CSS trick: forces scroll anchor to the bottom */
}
.terminal-content {
    display: flex;
    flex-direction: column;
}
"""

# =====================================================================
# 5. GRADIO BLOCKS LAYOUT
# =====================================================================

with gr.Blocks(title="Pi Network Manager", css=custom_css) as demo:
    gr.Markdown("# 📶 Raspberry Pi Network Controller")
    
    with gr.Row():
        # Left Panel: Operational Feeds
        with gr.Column(scale=2):
            gr.Markdown("### Live System Output")
            status_display = gr.Textbox(label="Internet Status", value="Checking...", interactive=False)
            
            # Use gr.HTML inside a styled wrapper instead of TextArea for true terminal capabilities
            gr.Markdown("**Console Stream**")
            console_log = gr.HTML(
                value="<div class='terminal-box'><div class='terminal-content'>Awaiting logs...</div></div>"
            )
        
        # Right Panel: Setup Configurations
        with gr.Column(scale=1):
            gr.Markdown("### Add WPA Network")
            ssid_input = gr.Textbox(label="SSID (Network Name)", placeholder="e.g. Home_WiFi")
            psk_input = gr.Textbox(label="WPA Password", type="password", placeholder="••••••••")
            submit_btn = gr.Button("Save & Connect", variant="primary")
            form_output = gr.Markdown()

    # Form interactive actions
    submit_btn.click(
        fn=connect_to_network,
        inputs=[ssid_input, psk_input],
        outputs=form_output
    )
    
    # Modify update UI helper to wrap incoming text into our CSS terminal structure
    def ui_updater_wrapper():
        logs, status = update_dashboard()
        html_wrapped_logs = f"<div class='terminal-box'><div class='terminal-content'>{logs}</div></div>"
        return html_wrapped_logs, status

    refresh_timer = gr.Timer(value=2.0)
    refresh_timer.tick(
        fn=ui_updater_wrapper,
        inputs=None,
        outputs=[console_log, status_display]
    )

# Run the app locally over the network interface
demo.launch(server_name="0.0.0.0", server_port=7860)
