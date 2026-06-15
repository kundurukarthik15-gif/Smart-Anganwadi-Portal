import urllib.request
import os

url = "https://raw.githubusercontent.com/kundurukarthik15-gif/Smart-Anganwadi-Portal/main/index.html"
local_file = "index.html"

try:
    print(f"Downloading original index.html from {url}...")
    with urllib.request.urlopen(url) as response:
        html_content = response.read()
    
    # Backup existing index.html just in case
    if os.path.exists(local_file):
        backup_file = local_file + ".bak"
        print(f"Creating backup of local file as {backup_file}...")
        with open(local_file, "rb") as f_src:
            with open(backup_file, "wb") as f_dst:
                f_dst.write(f_src.read())
                
    print(f"Writing to local {local_file}...")
    with open(local_file, "wb") as f_out:
        f_out.write(html_content)
        
    print(f"Success! Restored index.html to its original complete state ({len(html_content)} bytes).")
except Exception as e:
    print(f"Error restoring file: {e}")
