# MCP Obsidian Note Database

The purpose of this project is to automatically link up my notes, projects and context up to LLM's in a seamless way.

Right now its utility is pretty low.

## Issues

- The pdf extraction is pretty bad for handwritten text, this implementation is currently only useful for markdown files.

- As of 2025-03-03: Anthropic is the only major LLM provider to support MCP in their desktop app, and the desktop app is terrible and this MCP integration hits Claude's scarce usage limits quickly.

## Configuration

If using claude desktop, go to settings, developer, and edit the config file "claude_desktop_config.json".

Here is an example config:

```json
{
  "mcpServers": {
    "notes": {
      "command": "PATH-TO-MCP-PROJECT/.venv/bin/python",
      "args": ["PATH-TO-MCP-PROJECT/notes_mcp_server.py"]
    }
  }
}
```

## Example Usage

Example Prompt:
Looking at my notes, how can I accomplish my career goals?

Example Response:

I'll help you analyze your notes to develop a plan for accomplishing your career goals. Let me first check what notes you have available.

_list_files tool call_

I see you have several files that could help us understand your career goals and plans. Let me first check your career-related notes and personal context to get a better understanding of what you want to achieve.

_read_markdown tool call_

Now let me check your goals file and context about yourself for additional information:

_read_markdown tool call_

Let me also check your project details to understand what you're working on:

_read_markdown tool call_

GENERAL ADVICE SPECIFIC TO CAREER GOALS

## Next Steps

Right now the Claude desktop app is the only frontier lab llm interface with direct support for MCP (that I know of). The claude desktop app is terrible and buggy and the MCP integration is slow and hits usage limits fast.

Based on twitter comments I am hoping ChatGPT integrates MCP into their desktop app, and Gemini makes a desktop app.

I also am looking forward to better open source MCP integrations, I think it is becoming the standard for LLM <-> Client <-> Server interaction.
