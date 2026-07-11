def bytes_to_gb(num_bytes: int) -> float:
    """
    Convert bytes to Gigabytes.
    
    Args:
        num_bytes: The integer size in bytes.
        
    Returns:
        The float representation in Gigabytes.
    """
    return num_bytes / (1024 ** 3)


def gb_to_bytes(gb: float) -> int:
    """
    Convert Gigabytes to bytes.
    
    Args:
        gb: The float size in Gigabytes.
        
    Returns:
        The integer representation in bytes.
    """
    return int(gb * (1024 ** 3))
