# Integration example for search feature
# This shows how to integrate the search module into the main project

"""
To integrate the search feature into your main project:

1. In ai/ai_engine.py, add:
   from search.prompts import SEARCH_PROMPT
   from search.file_search import search_files, format_search_results
   import os

   And add the search mode before chat mode:
   # -------------------------
   # SEARCH MODE
   # -------------------------
   search_keywords = ["search", "find", "locate", "grep", "look for"]
   if any(keyword in query_lower for keyword in search_keywords):
       # Perform file search
       search_results = search_files(query, base_path=os.getcwd())
       search_context = format_search_results(search_results)

       prompt = SEARCH_PROMPT
       prompt = prompt.replace("{query}", query)
       prompt = prompt.replace("{context}", search_context)

       return ask_ollama(prompt, mode="search")

2. In core/command_handler.py, add:
   from search.file_search import search_files, format_search_results
   from ai.ai_engine import ask_ai

   And add before natural_result:
   if query.startswith("search "):
       search_query = query[7:].strip()
       if not search_query:
           return "Please provide a search query. Usage: ai: search <query>"

       # Get project context
       context = detect_context()
       os_type = get_os()

       # Use AI to analyze search results
       return ask_ai(f"search {search_query}", context, os_type)

3. Update the help text in command_handler.py to include:
   Search
   ------
   ai: search <query>    Search files and analyze content with AI
"""

# Example usage
if __name__ == "__main__":
    from file_search import search_files, format_search_results

    # Test search
    results = search_files("def", ".")
    print(f"Found {len(results)} files with matches")

    # Format results
    formatted = format_search_results(results)
    print("Sample formatted output:")
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)