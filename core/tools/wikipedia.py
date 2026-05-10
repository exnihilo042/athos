import wikipedia

def search_wikipedia(query, sentences=2):
    """
    Search Wikipedia for a query and return a summary.

    Args:
        query (str): The search query.
        sentences (int): Number of sentences to return.

    Returns:
        str: Summary from Wikipedia.
    """
    try:
        return wikipedia.summary(query, sentences=sentences)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Disambiguation: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return "Page not found."
    except Exception as e:
        return f"Error: {str(e)}"