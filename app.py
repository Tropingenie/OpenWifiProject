import queue
import logging
import logging.handlers
import time
import threading
import subprocess
import gradio as gr

from main import main

# =====================================================================
# 1. LOGGING & QUEUE SETUP
# =====================================================================

# Define the global queue that will buffer log records
log_queue = queue.Queue()

# Get the specific logger you defined in your pseudocode
logger = logging.getLogger("gradio app")
logger.setLevel(logging.INFO)

# Create the QueueHandler and link it to our thread-safe queue
queue_handler = logging.handlers.QueueHandler(log_queue)
logger.addHandler(queue_handler)

# Optional: Add a stream handler so you still see logs in the Pi terminal
console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', '%H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(console_formatter)
logger.addHandler(stream_handler)


# =====================================================================
# 2. BACKGROUND SCRIPT SIMULATION (Uses native logger)
# =====================================================================

def run_network_script_mock():
    """Simulates your background python script firing native log events."""
    logger.info("Initializing network cleaner...")
    while True:
        time.sleep(3)
        logger.info("Scanning via nmcli...")
        time.sleep(4)
        logger.warning("Cleaning up NetworkManager profiles...")

# Spin up your background tasks
threading.Thread(target=main, daemon=True).start()


# =====================================================================
# 3. INTERFACE LOGIC
# =====================================================================

def get_internet_status():
    """Checks if the Pi is truly online by pinging Google's DNS."""
    try:
        subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "🟢 Online"
    except subprocess.CalledProcessError:
        return "🔴 Offline"

# Persistent cache to hold the console history between UI refreshes
log_history = []

def update_dashboard():
    """Drains the log queue and fetches internet status."""
    global log_history
    
    # Drain the QueueHandler's buffered log items
    while not log_queue.empty():
        try:
            # QueueHandler puts full LogRecord objects into the queue
            record = log_queue.get_nowait()
            
            # Format the record into a human-readable text line
            formatted_line = f"[{time.strftime('%H:%M:%S', time.localtime(record.created))}] {record.getMessage()}"
            log_history.append(formatted_line)
        except queue.Empty:
            break
            
    # Tail the last 15 lines so the box doesn't grow forever
    visible_logs = "\n".join(log_history[-15:])
    
    return visible_logs, get_internet_status()

def connect_to_network(ssid, password):
    """Triggered when the user submits a manual network configuration."""
    logger.info(f"Manual connection request submitted for SSID: {ssid}")
    
    # Your core nmcli hook goes here:
    # subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password])
    
    return f"Successfully sent request to connect to network: '{ssid}'"


# =====================================================================
# 4. GRADIO BLOCKS LAYOUT (Fixed for modern Gradio versions)
# =====================================================================

with gr.Blocks(title="Pi Network Manager") as demo:
    gr.Markdown("# 📶 Raspberry Pi Network Controller")
    
    with gr.Row():
        # Left Panel: Operational Feeds
        with gr.Column(scale=2):
            gr.Markdown("### Live System Output")
            status_display = gr.Textbox(label="Internet Status", value="Checking...", interactive=False)
            console_log = gr.TextArea(label="Console Stream", lines=12, max_lines=12, interactive=False, placeholder="Awaiting logs...")
        
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
    
    # FIX: Define an explicit Timer component to drive the refresh cycle instead of using .load(every=...)
    refresh_timer = gr.Timer(value=2.0)
    
    # Hook the timer up to execute your updates repeatedly every 2 seconds
    refresh_timer.tick(
        fn=update_dashboard,
        inputs=None,
        outputs=[console_log, status_display]
    )

# Run the app locally over the network interface
demo.launch(server_name="0.0.0.0", server_port=7860)
