import webbrowser

def search_youtube(query):
    """
    Search YouTube for a query by opening the search page in browser.

    Args:
        query (str): The search query.
    """
    url = f"https://www.youtube.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opened YouTube search for: {query}"