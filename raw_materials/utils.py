"""
Utility functions for raw materials app
"""
from decimal import Decimal, InvalidOperation

def safe_decimal_conversion(value, default='0.0'):
    """
    Safely convert a value to Decimal, returning a default value if conversion fails
    
    Args:
        value: The value to convert to Decimal
        default: Default value to use if conversion fails (default: '0.0')
        
    Returns:
        Decimal object
    """
    if value is None:
        return Decimal(default)
    
    # If it's already a Decimal, return it as is
    if isinstance(value, Decimal):
        return value
        
    try:
        # Clean the input - replace commas with dots and strip whitespace
        if isinstance(value, str):
            # Remove any non-numeric characters except for the decimal point
            value = value.replace(',', '.').strip()
            # Additional cleaning for potential invalid inputs
            value = ''.join([c for c in value if c.isdigit() or c == '.'])
            # Ensure only one decimal point
            if value.count('.') > 1:
                parts = value.split('.')
                value = parts[0] + '.' + ''.join(parts[1:])
            
        # Always convert through string representation to avoid float precision issues
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to convert '{value}' to Decimal. Using default: {default}")
        return Decimal(default)
