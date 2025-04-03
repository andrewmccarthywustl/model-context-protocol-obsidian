# note_utils.py
import os
import glob
import re
import sys
from config import VAULT_PATH, INCLUDE_YAML_FRONTMATTER, MAX_SEARCH_RESULTS

# --- Note Utility Functions ---

def get_all_notes():
    try:
        if not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH:
            if VAULT_PATH and VAULT_PATH != os.path.expanduser("~/Documents/MISSING_VAULT"):
                 print(f"Error (note_utils): VAULT_PATH is not configured or accessible: {VAULT_PATH}", file=sys.stderr)
            return []
        abs_vault_path = os.path.abspath(VAULT_PATH)
        notes_pattern = os.path.join(abs_vault_path, "**/*.md")
        absolute_paths = glob.glob(notes_pattern, recursive=True)
        relative_paths = []
        for abs_path in absolute_paths:
            if os.path.isfile(abs_path):
                rel_path = os.path.relpath(abs_path, abs_vault_path)
                relative_paths.append(rel_path.replace(os.path.sep, '/'))
        return sorted(relative_paths)
    except Exception as e:
        print(f"Error in get_all_notes: {str(e)}", file=sys.stderr)
        return []

def get_note_content(relative_note_path):
    try:
        if not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH:
             return None
        full_path = os.path.join(VAULT_PATH, relative_note_path)
        # Ensure it's specifically an MD file for this context if needed,
        # but basic check happens before calling open()
        if not os.path.isfile(full_path):
            return None
        # Add check for MD extension if called only for MD files now
        if not relative_note_path.lower().endswith('.md'):
             print(f"Warning (get_note_content): Attempted to read non-markdown file as text: {relative_note_path}", file=sys.stderr)
             # Return None or raise error, depending on desired strictness
             return None

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not INCLUDE_YAML_FRONTMATTER and content.startswith('---'):
            end_marker = content.find('\n---', 3)
            if end_marker > 0:
                content = content[end_marker+4:].strip()
        return content
    except Exception as e:
        print(f"Error in get_note_content for '{relative_note_path}': {str(e)}", file=sys.stderr)
        return None

def search_notes_content(query):
    try:
        results = []
        if not query or not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH: return []
        query_lower = query.lower()
        # This searches ONLY markdown files because get_all_notes only returns markdown
        for note_path in get_all_notes():
            content = get_note_content(note_path)
            if content and query_lower in content.lower():
                results.append(note_path)
                if len(results) >= MAX_SEARCH_RESULTS: break
        return results
    except Exception as e:
        print(f"Error in search_notes_content: {str(e)}", file=sys.stderr)
        return []

def extract_tags():
    try:
        if not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH: return []
        all_tags = set()
        tag_pattern = r'#([a-zA-Z][a-zA-Z0-9_-]*)'
        # This searches ONLY markdown files because get_all_notes only returns markdown
        for note_path in get_all_notes():
            content = get_note_content(note_path)
            if content:
                found_tags = re.findall(tag_pattern, content)
                all_tags.update(found_tags)
        return sorted(list(all_tags))
    except Exception as e:
        print(f"Error in extract_tags: {str(e)}", file=sys.stderr)
        return []