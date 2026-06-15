filepath = "script.js"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

match = content.find("loginWithGoogle")
if match != -1:
    print(f"Found loginWithGoogle at index {match}")
    # Write 100 lines starting from match
    lines = content[match:].splitlines()[:60]
    with open("google_login_func.txt", "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
    print("Generated google_login_func.txt")
else:
    print("loginWithGoogle function not found.")
