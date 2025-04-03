# notes_mcp_server.py (Renamed read_note to read_markdown)
import os
import sys
import glob
import urllib.parse
# import base64 # No longer needed unless adding back blob resources
import json

# --- PyMuPDF Import ---
try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: Failed to import fitz (PyMuPDF). Install with 'pip install pymupdf'", file=sys.stderr)
    sys.exit(1)

# --- MCP Imports ---
try:
    from mcp.server.fastmcp import FastMCP, Context
except ImportError:
    print("ERROR: Failed to import FastMCP. Make sure it's installed.", file=sys.stderr)
    sys.exit(1)

# --- Project Imports ---
try:
    from config import VAULT_PATH
except ImportError:
     print("ERROR: Could not import VAULT_PATH from config.py.", file=sys.stderr)
     sys.exit(1)

try:
    from note_utils import get_note_content
except ImportError:
    print("ERROR: Could not import from note_utils.py.", file=sys.stderr)
    sys.exit(1)


# --- Server Setup ---
print(f"NOTES MCP SERVER: Starting up...", file=sys.stderr)
print(f"NOTES MCP SERVER: Using vault path: {VAULT_PATH}", file=sys.stderr)

if not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH:
     print(f"ERROR: The VAULT_PATH '{VAULT_PATH}' is not valid.", file=sys.stderr)
     sys.exit(1)
print(f"NOTES MCP SERVER: Vault path confirmed.", file=sys.stderr)

mcp = FastMCP("Notes")


# --- Path Security Utilities ---
def _sanitize_path(path: str) -> str:
    # (Implementation as before)
    if not path: raise ValueError("Path cannot be empty.")
    decoded_path = urllib.parse.unquote(path)
    norm_path = os.path.normpath(decoded_path)
    if ".." in norm_path.split(os.path.sep) or os.path.isabs(norm_path):
        print(f"SECURITY WARNING: Path traversal/absolute path blocked: {path}", file=sys.stderr)
        raise ValueError("Invalid or potentially unsafe path requested.")
    if os.path.isabs(decoded_path): raise ValueError("Invalid or potentially unsafe path requested.")
    return decoded_path

def _ensure_path_within_vault(full_path_to_check: str):
    # (Implementation as before)
    abs_full_path = os.path.abspath(full_path_to_check)
    abs_vault_root = os.path.abspath(VAULT_PATH)
    if not abs_full_path.startswith(abs_vault_root + os.path.sep) and abs_full_path != abs_vault_root:
        print(f"SECURITY ERROR: Path outside vault blocked: '{abs_full_path}'", file=sys.stderr)
        raise ValueError("Access denied: Path is outside the configured vault.")


# --- MCP Tools ---

@mcp.tool()
def list_files(file_types: str = "md,pdf") -> str: # Default includes md and pdf
    """LLM INSTRUCTIONS for list_files:
    1. PURPOSE: Use me to find files by searching file paths. Defaults to listing Markdown (.md) and PDF (.pdf) files.
    2. PARAMETERS: 'file_types' (string, optional, comma-separated). Examples: 'md', 'pdf', 'md,pdf,png'.
    3. OUTPUT: JSON STRING list of objects: '[{"filename": "name.ext", "path": "relative/path/name.ext"}, ...]'. Contains 'filename' for display and 'path' (RELATIVE path).
    4. USING THE OUTPUT: Extract the 'path' for the desired file. Use 'read_markdown' for '.md' files and 'read_pdf' for '.pdf' files, passing the relative path to the appropriate tool.
    """
    print(f"MCP TOOL: Request received for list_files (types: '{file_types}')", file=sys.stderr)
    try:
        if not VAULT_PATH or not os.path.isdir(VAULT_PATH) or "MISSING_VAULT" in VAULT_PATH:
             return json.dumps({"error": "Vault path is not configured or accessible."})
        allowed_extensions = [ext.strip().lower().lstrip('.') for ext in file_types.split(',') if ext.strip()]
        if not allowed_extensions: return json.dumps({"error": "No valid file types specified."})
        search_results = []
        abs_vault_path = os.path.abspath(VAULT_PATH)
        for extension in allowed_extensions:
            pattern = os.path.join(abs_vault_path, "**", f"*.{extension}")
            found_paths = glob.glob(pattern, recursive=True)
            for abs_path in found_paths:
                if os.path.isfile(abs_path) and os.path.abspath(abs_path).startswith(abs_vault_path + os.path.sep):
                    relative_path_orig = os.path.relpath(abs_path, abs_vault_path)
                    relative_path_clean = relative_path_orig.replace(os.path.sep, '/')
                    search_results.append({"filename": os.path.basename(relative_path_orig),"path": relative_path_clean})
        if not search_results: return json.dumps({"message": f"No files found matching types '{file_types}'."})
        search_results.sort(key=lambda x: x['path'])
        return json.dumps(search_results)
    except Exception as e:
        print(f"Error in list_files tool: {str(e)}", file=sys.stderr)
        return json.dumps({"error": f"Error listing files: {str(e)}"})

# RENAMED read_note to read_markdown
@mcp.tool()
def read_markdown(note_path: str) -> str: # <-- Renamed function
    """LLM Instructions for read_markdown: # <-- Updated docstring title
    1. PURPOSE: Reads and returns the text content of a specific MARKDOWN (.md) note file.
    2. INPUT: Takes the RELATIVE 'note_path' (e.g., 'folder/my_note.md') obtained from the 'list_files' tool.
    3. OUTPUT: Returns the full text content as a string, or an error message.
    4. IMPORTANT: This tool ONLY works for '.md' files. Use 'read_pdf' for PDF files.
    """
    # <-- Updated log message
    print(f"MCP TOOL: Request received for read_markdown tool with path: {note_path}", file=sys.stderr)
    try:
        safe_relative_path = _sanitize_path(note_path)
        # Explicitly check for .md extension for this tool
        if not safe_relative_path.lower().endswith('.md'):
             # <-- Updated tool name in error message
             return f"Error: The read_markdown tool only works for Markdown (.md) files. Cannot read '{safe_relative_path}'."

        full_path = os.path.join(VAULT_PATH, safe_relative_path)
        _ensure_path_within_vault(full_path) # Security check

        # Use the utility function to get content (handles errors and YAML)
        content = get_note_content(safe_relative_path) # From note_utils

        if content is None:
            if not os.path.exists(full_path):
                 return f"Error: Markdown file not found at path: {safe_relative_path}"
            else:
                 return f"Error: Could not read Markdown content from path: {safe_relative_path}. Check server logs."
        return content
    except ValueError as e: # Catch path validation errors
         print(f"Error in read_markdown tool path validation: {str(e)}", file=sys.stderr) # <-- Updated log message source
         return f"Error: Invalid path provided. {str(e)}"
    except Exception as e:
        print(f"Unexpected error in read_markdown tool for '{note_path}': {str(e)}", file=sys.stderr) # <-- Updated log message source
        return f"Error reading Markdown note: {str(e)}"


@mcp.tool()
def read_pdf(pdf_path: str) -> str:
    """LLM Instructions for read_pdf:
    1. PURPOSE: Extracts text content from a PDF file using PyMuPDF (fitz) library. Prioritizes extracting embedded digital text.
    2. INPUT: Takes the RELATIVE 'pdf_path' (e.g., 'folder/document.pdf') obtained from the 'list_files' tool.
    3. ACTION: Opens the PDF and extracts text directly from each page. This is generally fast and accurate for digitally created PDFs. It does NOT perform OCR on image-only PDFs.
    4. OUTPUT: Returns the extracted text as a single string, concatenated from all pages, or an error message.
    5. IMPORTANT: This tool ONLY works for '.pdf' files. Use 'read_markdown' for Markdown files. It will return empty or minimal text for scanned/image-only PDFs.
    """
    print(f"MCP TOOL: Request received for read_pdf tool with path: {pdf_path}", file=sys.stderr)
    # (Implementation using PyMuPDF is the same as previous version)
    try:
        safe_relative_path = _sanitize_path(pdf_path)
        if not safe_relative_path.lower().endswith('.pdf'):
            return f"Error: The read_pdf tool only works for PDF (.pdf) files. Cannot read '{safe_relative_path}'."
        full_path = os.path.join(VAULT_PATH, safe_relative_path)
        _ensure_path_within_vault(full_path)
        if not os.path.isfile(full_path):
             return f"Error: PDF file not found at path: {safe_relative_path}"
        print(f"MCP TOOL: Starting PDF text extraction using PyMuPDF for: {full_path}", file=sys.stderr)
        extracted_text = ""
        doc = None
        try:
            doc = fitz.open(full_path)
            page_count = len(doc)
            for page_num in range(page_count):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text")
                    extracted_text += f"--- Page {page_num + 1}/{page_count} ---\n{page_text}\n\n"
                except Exception as page_err:
                    print(f"Error extracting text from page {page_num + 1}: {page_err}", file=sys.stderr)
                    extracted_text += f"--- Page {page_num + 1}/{page_count} (Extraction Error) ---\n\n"
        except Exception as pdf_err:
             print(f"Error opening or processing PDF '{safe_relative_path}' with PyMuPDF: {pdf_err}", file=sys.stderr)
             return f"Error: Failed to process PDF file '{safe_relative_path}' using PyMuPDF: {pdf_err}"
        finally:
            if doc: doc.close()
        print(f"MCP TOOL: Finished PyMuPDF text extraction for: {full_path}. Extracted {len(extracted_text)} chars.", file=sys.stderr)
        if not extracted_text.strip():
             return f"No digital text content could be extracted from PDF: {safe_relative_path}. It might be an image-only or scanned document."
        return extracted_text.strip()
    except ValueError as e:
        print(f"Error in read_pdf tool path validation: {str(e)}", file=sys.stderr)
        return f"Error: Invalid path provided. {str(e)}"
    except Exception as e:
        print(f"Unexpected error in read_pdf tool for '{pdf_path}': {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error reading PDF: An unexpected error occurred. Check server logs."


# --- Run Server ---
if __name__ == "__main__":
    try:
        print("\nNOTES MCP SERVER (Tools for MD text & PDF direct text): Attempting to start...", file=sys.stderr)
        mcp.run()
        print("NOTES MCP SERVER: Server stopped.", file=sys.stderr)
    except Exception as e:
        print(f"\nFATAL ERROR: Failed to run MCP server: {str(e)}", file=sys.stderr)
        sys.exit(1)