import re

filepath = "script.js"
patterns = [
    r"localStorage\.setItem",
    r"localStorage\.getItem",
    r"token",
    r"login",
    r"session"
]

# Read script.js
for encoding in ["utf-8", "utf-16", "utf-16-le", "latin-1"]:
    try:
        with open(filepath, "r", encoding=encoding) as f:
            content = f.read()
        break
    except Exception:
        continue

lines = content.splitlines()

with open("script_auth_lines.txt", "w", encoding="utf-8") as out:
    for i, line in enumerate(lines):
        matched = False
        for p in patterns:
            if re.search(p, line, re.IGNORECASE):
                matched = True
                break
        if matched:
            out.write(f"Line {i+1}: {line.strip()[:200]}\n")

print("Generated script_auth_lines.txt successfully.")
