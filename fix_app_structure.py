#!/usr/bin/env python3
"""
Fix app.py by moving endpoint definitions before if __name__ == '__main__':
"""

# Read the file
with open('app.py', 'r') as f:
    lines = f.readlines()

# Find the if __name__ == '__main__': line
main_block_start = None
for i, line in enumerate(lines):
    if line.strip() == "if __name__ == '__main__':":
        main_block_start = i
        break

if main_block_start is None:
    print("Could not find main block!")
    exit(1)

# Find where the endpoints start after main block  
endpoint_marker = "# ========== SESSION MANAGEMENT ENDPOINTS =========="
endpoint_start = None
for i in range(main_block_start, len(lines)):
    if endpoint_marker in lines[i]:
        endpoint_start = i
        break

if endpoint_start is None:
    print("Endpoints are already in correct position or not found!")
    exit(0)

print(f"Found main block at line {main_block_start + 1}")
print(f"Found endpoints at line {endpoint_start + 1}")

# Extract the three sections
before_main = lines[:main_block_start]
main_block = lines[main_block_start:endpoint_start]
endpoints = lines[endpoint_start:]

# Reconstruct: before_main + endpoints + main_block
new_lines = before_main + endpoints + ['\n'] + main_block

# Write back
with open('app.py', 'w') as f:
    f.writelines(new_lines)

print(f"File restructured successfully!")
print(f"- Original lines: {len(lines)}")
print(f"- After restructure: {len(new_lines)}")
