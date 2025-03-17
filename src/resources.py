import sys
import os

def resource_path(relative_path):
    """
    Returns the absolute path to a resource, compatible with PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temporary folder and stores path in _MEIPASS.
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)
