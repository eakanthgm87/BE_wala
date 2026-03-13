import os

from ai.ollama_client import ask_ollama

from .file_search import search_files, format_search_results
from .prompts import SEARCH_PROMPT


def normalize_search_query(query: str) -> str:
    """Normalize a user query to a clean search term."""
    q = query.lower().strip()

    # Strip leading 'search' keyword
    if q.startswith("search "):
        q = q[len("search "):].strip()

    # Remove common filler words
    for token in ["file", "files", "folder", "folders", "directory", "directories", "project"]:
        if q.endswith(" " + token):
            q = q[: -len(token)].strip()

    return q


def ai_search(query: str, base_path: str = ".") -> str:
    """Perform a project search and use the local Ollama model to summarize results.

    This returns both the raw search matches (filenames + snippet context)
    and a short AI summary.
    """

    search_term = normalize_search_query(query)

    # Search project files for the query
    results = search_files(search_term, base_path=base_path)
    search_context = format_search_results(results)

    # If we found nothing, return a deterministic message (no AI needed)
    if not results:
        return (
            f"No matches found for '{search_term}'.\n"
            "Try using a different term or broaden the search (e.g., remove extra words)."
        )

    # If we did find matches, return the raw results only (no AI summary).
    # This ensures you always see the real output.
    output = ["SEARCH RESULTS:", search_context]
    return "\n".join(output)
