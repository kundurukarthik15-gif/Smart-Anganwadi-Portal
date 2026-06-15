import urllib.request

url = "https://raw.githubusercontent.com/kundurukarthik15-gif/Smart-Anganwadi-Portal/main/index.html"
try:
    print(f"Downloading {url}...")
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
    print(f"Downloaded {len(html)} characters ({len(html.splitlines())} lines).")
    print("Last 10 lines of GitHub file:")
    lines = html.splitlines()
    for l in lines[-10:]:
        print(l)
except Exception as e:
    print(f"Error: {e}")
