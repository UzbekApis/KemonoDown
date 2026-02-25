"""
Search module for Kemono WebApp
Implements Levenshtein distance algorithm for fuzzy artist search
"""

from typing import List, Dict, Any, Union


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to change one string
    into another.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        int: The Levenshtein distance between s1 and s2
        
    Example:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("hello", "hello")
        0
    """
    # Handle empty strings
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    
    # Create matrix for dynamic programming
    len1, len2 = len(s1), len(s2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    # Initialize first column and row
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    # Fill the matrix
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # deletion
                matrix[i][j - 1] + 1,      # insertion
                matrix[i - 1][j - 1] + cost  # substitution
            )
    
    return matrix[len1][len2]


def find_closest_matches(
    search_term: str,
    items: List[Union[Dict, Any]],
    key: str = 'name',
    limit: int = 10
) -> List[Union[Dict, Any]]:
    """
    Find closest matches to search term using Levenshtein distance.
    
    This function implements fuzzy search by calculating the edit distance
    between the search term and each item's name field. Results are sorted
    by distance (closest matches first) and limited to the specified count.
    
    Args:
        search_term: The string to search for
        items: List of items to search through (can be dicts or objects)
        key: The key/attribute name to compare against (default: 'name')
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        List of items sorted by closest match (lowest distance first)
        
    Example:
        >>> artists = [
        ...     {'name': 'John Doe', 'id': 1},
        ...     {'name': 'Jane Smith', 'id': 2},
        ...     {'name': 'John Smith', 'id': 3}
        ... ]
        >>> find_closest_matches('jon', artists, limit=2)
        [{'name': 'John Doe', 'id': 1}, {'name': 'John Smith', 'id': 3}]
    """
    results = []
    
    # Convert search term to lowercase for case-insensitive comparison
    search_lower = search_term.lower()
    
    for item in items:
        # Extract the name from the item
        # Support both dict and object access
        if isinstance(item, dict):
            name = item.get(key, '')
        elif hasattr(item, key):
            name = getattr(item, key, '')
        else:
            # If item is a simple string
            name = str(item)
        
        # Skip empty names
        if not name:
            continue
        
        # Calculate Levenshtein distance (case-insensitive)
        distance = levenshtein_distance(search_lower, name.lower())
        
        # Store result with distance
        results.append({
            'data': item,
            'distance': distance
        })
    
    # Sort by distance (ascending - closest matches first)
    results.sort(key=lambda x: x['distance'])
    
    # Return only the data portion of top matches
    top_matches = results[:limit]
    return [match['data'] for match in top_matches]
