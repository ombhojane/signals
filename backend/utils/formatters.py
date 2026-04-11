"""
Formatting Utilities - Number and percentage formatting for display.
"""

from typing import Any, Optional


def format_number(value: Any) -> str:
    """Format numbers for display with K/M suffixes.
    
    Args:
        value: Any numeric value
        
    Returns:
        Formatted string (e.g., "$1.23M", "$456.78K")
    """
    if value is None:
        return "N/A"
    
    try:
        num = float(value)
        if num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num/1_000:.2f}K"
        else:
            return f"${num:.4f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Any) -> str:
    """Format percentage values for display.
    
    Args:
        value: Any numeric value representing a percentage
        
    Returns:
        Formatted percentage string (e.g., "15.50%")
    """
    if value is None:
        return "N/A"
    
    try:
        num = float(value)
        return f"{num:.2f}%"
    except (ValueError, TypeError):
        return str(value)


def print_section_header(title: str) -> None:
    """Print a formatted section header to console.
    
    Args:
        title: Section title to display
    """
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)


def print_subsection(title: str) -> None:
    """Print a formatted subsection header to console.
    
    Args:
        title: Subsection title to display
    """
    print(f"\n--- {title} ---")


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float.
    
    Args:
        value: Any value to convert
        
    Returns:
        Float value or None if conversion fails
    """
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int.
    
    Args:
        value: Any value to convert
        
    Returns:
        Int value or None if conversion fails
    """
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None
