"""
This is where I thrown in various file methods that multiple classes use.
"""

# Handle imports
import os

# Define methods
def get_absolute_path():
    """
    Get the absolute path of this Python file.
    """
    absolute_path = os.path.dirname(os.path.abspath(__file__)) # != os.path.abspath("./")
    if absolute_path != "/":
        absolute_path += "/"

    return absolute_path