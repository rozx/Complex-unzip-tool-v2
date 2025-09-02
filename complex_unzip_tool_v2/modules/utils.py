from difflib import SequenceMatcher

def getStringSimilarity(str1, str2):
    """
    Calculate similarity between two strings using SequenceMatcher.
    
    Args:
        str1 (str): First string to compare
        str2 (str): Second string to compare
    
    Returns:
        float: Similarity ratio between 0.0 (no similarity) and 1.0 (identical)
    """
    if not str1 and not str2:
        return 1.0
    if not str1 or not str2:
        return 0.0
    
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()