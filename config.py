# config.py
import os
import sys

# --- Configuration Settings ---
POTENTIAL_VAULT_PATHS = [
    #This is the default path to obsidian stored on icloud drive, if your vault is not located here, change it.
    os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/YOUR-VAULT-NAME"),
]
VAULT_PATH = None
for path in POTENTIAL_VAULT_PATHS:
    if path and os.path.exists(path) and os.path.isdir(path):
        VAULT_PATH = path
        break
if VAULT_PATH is None:
    print("="*60, file=sys.stderr)
    print("ERROR: Could not find a valid Obsidian vault directory.", file=sys.stderr)
    VAULT_PATH = os.path.expanduser("~/Documents/MISSING_VAULT")
    print(f"WARNING: Using placeholder VAULT_PATH: {VAULT_PATH}", file=sys.stderr)
MAX_SEARCH_RESULTS = 50
INCLUDE_YAML_FRONTMATTER = True
print(f"CONFIG: Using VAULT_PATH: {VAULT_PATH}", file=sys.stderr)