import os

keywords = ["google", "localhost", "127.0.0.1", "redirect"]

for root, dirs, files in os.walk("."):
    # Skip standard ignored directories
    if any(p in root for p in [".git", "__pycache__", ".venv", "node_modules"]):
        continue
    for file in files:
        if file.endswith((".py", ".js", ".html", ".css", ".sql")):
            filepath = os.path.join(root, file)
            try:
                # Try reading in different encodings
                for encoding in ["utf-8", "utf-16", "utf-16-le", "latin-1"]:
                    try:
                        with open(filepath, "r", encoding=encoding) as f:
                            content = f.read()
                        break
                    except Exception:
                        continue
                
                # Check for keywords
                for kw in keywords:
                    if kw in content.lower():
                        # Find matching lines
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if kw in line.lower():
                                print(f"🔍 Found '{kw}' in {filepath} (Line {i+1}):")
                                print(f"   {line.strip()[:150]}")
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
