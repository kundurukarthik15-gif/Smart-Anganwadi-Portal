import os
import re

print("=== Smart Anganwadi Portal — Auth Redirect Troubleshooter ===")

# Search patterns
patterns = {
    "Supabase Auth Client": r"auth\.sign",
    "Redirect URLs": r"redirect",
    "Google OAuth": r"google",
    "Localhost References": r"localhost|127\.0\.0\.1",
    "Window Location Origin": r"window\.location\.origin"
}

found = False

# Scan files
for root, dirs, files in os.walk("."):
    if any(p in root for p in [".git", "__pycache__", ".venv", "node_modules"]):
        continue
    for file in files:
        if file.endswith((".py", ".js", ".html")):
            filepath = os.path.join(root, file)
            
            # Read file with proper encoding
            content = None
            for encoding in ["utf-8", "utf-16", "utf-16-le", "latin-1"]:
                try:
                    with open(filepath, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except Exception:
                    continue
            
            if content is None:
                continue
                
            # Search patterns
            for title, pattern in patterns.items():
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    for match in matches:
                        # Get surrounding line
                        start = max(0, content.rfind("\n", 0, match.start()))
                        end = content.find("\n", match.end())
                        if end == -1:
                            end = len(content)
                        line = content[start:end].strip()
                        
                        # Get line number
                        line_no = content.count("\n", 0, match.start()) + 1
                        
                        print(f"🔍 {title} in {filepath} (Line {line_no}):")
                        print(f"   {line[:150]}")
                        found = True

if not found:
    print("No direct hardcoded localhost redirect URLs found in code files.")

print("\n--- Why are you seeing 'localhost refused to connect'? ---")
print("When using Supabase Google Sign-In, Supabase redirects the browser back to your site after login.")
print("If it redirects to 'localhost:5000' (your local PC) instead of your new Render URL, it means:")
print("1. Your Supabase Authentication Site URL is still set to 'http://localhost:5000' in the Supabase Dashboard.")
print("2. Your Render URL is not added to the Redirect URLs list in the Supabase Dashboard.")
print("\n--- How to fix this in the Supabase Dashboard ---")
print("1. Log in to your Supabase Dashboard (https://supabase.com).")
print("2. Select your project: 'frwtmqkwmtnoibrnytrt'.")
print("3. Click on 'Authentication' (in the left sidebar) -> 'URL Configuration'.")
print("4. Update the 'Site URL' to your Render deployment URL (e.g., https://your-app-name.onrender.com).")
print("5. In the 'Redirect URLs' list, add your Render deployment URL (e.g., https://your-app-name.onrender.com/*).")
print("6. Click Save.")
print("\nOnce saved, Google Sign-In will redirect back to your live Render website instead of localhost!")
