def calculate_cross_jurisdiction_score(links):
    """
    Business logic for scoring a cross-jurisdiction link.
    """
    if not links:
        return 0.0
    return len(links) * 1.5  # Arbitrary weighting for demo purposes
