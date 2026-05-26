# OpenWifiProject/codegen.py
import os
import subprocess
import tempfile
from pathlib import Path

def get_active_ssid() -> str:
    """Uses nmcli to grab the raw SSID name of the active connection."""
    try:
        cmd = "nmcli -t -f ACTIVE,SSID dev wifi | awk -F: '$1==\"yes\"{print $2; exit}'"
        ssid = subprocess.check_output(cmd, shell=True, text=True).strip()
        return ssid if ssid else "Unknown_SSID"
    except Exception:
        return "Unknown_SSID"

def show_menu(title: str, options: list[str]) -> str:
    """Displays a simple command-line selection menu."""
    while True:
        print(f"\n--- {title} ---")
        for i, option in enumerate(options, 1):
            print(f" [{i}] {option}")
        
        choice = input(f"Select an option (1-{len(options)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("Invalid selection. Please try again.")

def generate_portal_flow():
    print("======================================")
    print("   OpenWifi Custom Codegen Utility    ")
    print("======================================")
    
    # 1. Grab current active SSID for automatic mapping
    current_ssid = get_active_ssid()
    print(f"📡 Detected Active Network: '{current_ssid}'")
    
    # 2. Structured Trigger URL Options
    url_menu_options = [
        "http://neverssl.com (Standard)",
        "http://connectivitycheck.gstatic.com/generate_204 (Android Style)",
        "Custom URL Entry"
    ]
    url_choice = show_menu("Choose Initial Trigger URL", url_menu_options)
    
    if "neverssl" in url_choice:
        target_url = "http://neverssl.com"
    elif "gstatic" in url_choice:
        target_url = "http://connectivitycheck.gstatic.com/generate_204"
    else:
        target_url = input("Enter custom URL: ").strip() or "http://neverssl.com"

    # 3. Get the Brand Identifier
    print("\n--- Portal Identity ---")
    brand_name = input(f"Enter brand name (default: {current_ssid}): ").strip()
    if not brand_name:
        brand_name = current_ssid if current_ssid != "Unknown_SSID" else "unnamed_portal"

    # 4. Setup Target Directory
    dest_dir = Path("Login Scripts") / "User"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    safe_filename = f"{brand_name.lower().replace(' ', '_')}_flow.py"
    final_output_path = dest_dir / safe_filename

    # 5. Launch Recorder
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_path = temp_file.name

    print(f"\n🚀 Launching visual recorder at: {target_url}")
    subprocess.run(["playwright", "codegen", "--target=python", "-o", temp_path, target_url])
    
    # 6. Clean and save with SSID metadata injection
    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
        sanitize_and_save(temp_path, final_output_path, current_ssid)
        print("\n✨ Generation Complete!")
        print(f"📁 Plugin saved to: {final_output_path}")
    else:
        print("\nRecording dropped or empty file returned.")
        
    if os.path.exists(temp_path):
        os.remove(temp_path)

def sanitize_and_save(source_path: str, dest_path: Path, ssid: str):
    """Parses raw code and injects metadata tags for automatic mapping."""
    with open(source_path, 'r') as f:
        lines = f.readlines()
        
    cleaned_lines = []
    in_run_function = False
    
    # Injected metadata header for our runner to scan
    cleaned_lines.append(f"ASSOCIATED_SSID = \"{ssid}\"\n\n")
    cleaned_lines.append("from playwright.sync_api import Page, expect\n")
    cleaned_lines.append("import re\n\n")
    cleaned_lines.append("def execute_flow(page: Page) -> None:\n")
    cleaned_lines.append("    \"\"\"Automatically generated via openwifi codegen wrapper.\"\"\"\n")
    
    for line in lines:
        if "def run(" in line:
            in_run_function = True
            continue
        if "context.close()" in line or "browser.close()" in line:
            break
        if in_run_function:
            if any(x in line for x in ["browser = ", "context = ", "page = "]):
                continue
            if line.startswith("    "):
                cleaned_lines.append(line)
            elif line.strip() == "":
                cleaned_lines.append("\n")

    with open(dest_path, 'w') as f:
        f.writelines(cleaned_lines)

if __name__ == "__main__":
    generate_portal_flow()
