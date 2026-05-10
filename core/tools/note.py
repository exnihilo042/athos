import os
from datetime import datetime

def take_note(note):
    """
    Take a note and append to notes.txt.

    Args:
        note (str): The note to take.
    """
    path = os.path.join(os.getcwd(), "notes.txt")
    with open(path, "a") as f:
        f.write(f"{datetime.now()}: {note}\n")
    return "Note taken."