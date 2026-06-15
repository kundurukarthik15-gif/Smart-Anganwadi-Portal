filepath = "script.js"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's find the auto login section
match = content.find("// ── AUTO LOGIN & VERIFICATION")
if match != -1:
    print(f"Found auto login section at index {match}")
    lines = content[match:].splitlines()[:60]
    with open("load_handler.txt", "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
    print("Generated load_handler.txt")
else:
    print("Auto login section not found.")
