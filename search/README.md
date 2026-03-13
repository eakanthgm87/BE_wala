# Search Feature for ShellMind AI Terminal

This module provides AI-powered file search functionality for the ShellMind AI Terminal project.

## Features

- **Intelligent File Search**: Searches through project files for specific content
- **AI Analysis**: Uses Ollama to analyze and summarize search results
- **Multiple File Types**: Supports Python, JavaScript, TypeScript, Java, JSON, YAML, Markdown, HTML, CSS, and text files
- **Context-Aware**: Provides line numbers and surrounding context for matches
- **Safety**: Ignores common directories like .git, node_modules, __pycache__, etc.

## Files

- `__init__.py` - Module initialization
- `file_search.py` - Core search functions
- `prompts.py` - AI prompts for search analysis
- `integration.py` - Instructions for integrating into main project
- `README.md` - This documentation

## Usage

### Direct Usage

```python
from search.file_search import search_files, format_search_results

# Search for content
results = search_files("function", ".")

# Format for display
formatted = format_search_results(results)
print(formatted)
```

### Integration with Main Project

See `integration.py` for detailed instructions on how to integrate this feature into the main ShellMind AI Terminal application.

### Command Usage

Once integrated, users can use:
- `ai: search function definitions`
- `ai: search error handling`
- `ai: search database connections`

## Configuration

- `MAX_FILE_SIZE`: Maximum file size to search (default: 10,000 bytes)
- `SUPPORTED_EXT`: File extensions to include in search
- `IGNORE_DIRS`: Directories to skip during search

## Dependencies

- Python 3.6+
- Ollama (for AI analysis when integrated)

## Testing

Run the integration script to test:
```bash
cd search
python integration.py
```