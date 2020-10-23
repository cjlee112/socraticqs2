"""
Configuration module containing providers keys.
"""

from dataclasses import dataclass


@dataclass
class Provider:
    """
    Providers name.
    """
    MULTICHOICE: int = 1
    CANVAS:      int = 2
    INTRO:       int = 3
    QUESTION:    int = 4
