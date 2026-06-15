import os

bak_file = "index.html.bak"
orig_file = "index.html" # Currently contains the original github file

try:
    print(f"Reading backup {bak_file}...")
    with open(bak_file, "r", encoding="utf-8") as f:
        bak_content = f.read()
        
    print(f"Reading original complete file {orig_file}...")
    with open(orig_file, "r", encoding="utf-8") as f:
        orig_content = f.read()
        
    # Find the matching point
    match_str = 'onclick="previewReport(\'dist\')"><i class="bi bi-eye-fill"></i>'
    
    idx_bak = bak_content.rfind(match_str)
    if idx_bak == -1:
        raise Exception(f"Could not find matching string '{match_str}' in backup file.")
        
    idx_orig = orig_content.find(match_str)
    if idx_orig == -1:
        raise Exception(f"Could not find matching string '{match_str}' in original file.")
        
    print(f"Found match in backup at index {idx_bak} and original at index {idx_orig}")
    
    # Slice the backup content up to the matching string + length of matching string
    merged_part1 = bak_content[:idx_bak + len(match_str)]
    
    # Slice the original content starting from the matching string + length of matching string
    merged_part2 = orig_content[idx_orig + len(match_str):]
    
    # Combine them
    merged_content = merged_part1 + merged_part2
    
    # Save to index.html
    with open("index.html", "w", encoding="utf-8") as f_out:
        f_out.write(merged_content)
        
    print(f"Successfully merged index.html!")
    print(f"New file size: {len(merged_content)} characters ({len(merged_content.splitlines())} lines).")
    
except Exception as e:
    print(f"Error during merge: {e}")
