filepath = "script.js"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's find the start of doLogin
match = content.find("async function doLogin")
if match == -1:
    match = content.find("function doLogin")

if match != -1:
    print(f"Found doLogin at index {match}")
    # Write 100 lines starting from match
    lines = content[match:].splitlines()[:120]
    with open("dologin_func.txt", "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
    print("Generated dologin_func.txt")
else:
    print("doLogin function not found directly. Searching for references...")
    # Find any line containing doLogin
    lines = content.splitlines()
    with open("dologin_func.txt", "w", encoding="utf-8") as out:
        for i, line in enumerate(lines):
            if "doLogin" in line:
                out.write(f"Line {i+1}: {line.strip()}\n")
