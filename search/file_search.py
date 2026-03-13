import os
import re
from typing import List, Dict

MAX_FILE_SIZE = 10000
SUPPORTED_EXT = (".py", ".js", ".ts", ".java", ".json", ".yaml", ".yml", ".md", ".txt", ".html", ".css")
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"}

def search_files(query: str, base_path: str = ".", max_results: int = 20) -> List[Dict]:
    """
    Search for query in project files and return matching snippets.

    Matches occur if the query appears in:
      - the file path/name
      - the file contents

    The query should typically be a short keyword or phrase.
    """
    results = []
    query_lower = query.lower().strip()

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if not file.endswith(SUPPORTED_EXT):
                continue

            path = os.path.join(root, file)
            try:
                if os.path.getsize(path) > MAX_FILE_SIZE:
                    continue

                file_lower = path.lower()
                matched_by_name = query_lower in file_lower

                matching_lines = []
                if not matched_by_name:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Simple text search (can be enhanced with regex)
                    if query_lower in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                # Get context around the match
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context = '\n'.join(lines[start:end])
                                matching_lines.append({
                                    'line': i + 1,
                                    'content': context
                                })

                if matched_by_name or matching_lines:
                    entry = {
                        'file': path,
                        'matches': matching_lines[:5] if matching_lines else []
                    }

                    if matched_by_name and not matching_lines:
                        entry['matches'] = [{'line': 0, 'content': '(filename match)'}]

                    results.append(entry)

                if len(results) >= max_results:
                    break

            except Exception:
                continue

    return results

def format_search_results(results: List[Dict]) -> str:
    """Format search results as a simple newline list of file paths."""
    if not results:
        return ""

    seen = set()
    lines = []

    for result in results:
        path = result.get('file')
        if not path or path in seen:
            continue
        seen.add(path)
        lines.append(path)

    return "\n".join(lines)