"""Input validators for prompts."""

import re
from urllib.parse import urlparse


def validate_url(url: str) -> bool | str:
    """Validate URL format.

    Args:
        url: URL string to validate.

    Returns:
        True if valid, error message string otherwise.
    """
    if not url:
        return "URL is required"

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    try:
        result = urlparse(url)
        if not result.netloc:
            return "Invalid URL format"
        return True
    except Exception:
        return "Invalid URL format"


def validate_slug(slug: str) -> bool | str:
    """Validate slug format (lowercase, alphanumeric, hyphens).

    Args:
        slug: Slug string to validate.

    Returns:
        True if valid, error message string otherwise.
    """
    if not slug:
        return "Value is required"

    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", slug.lower()):
        return "Must be lowercase alphanumeric with hyphens (e.g., my-org-name)"

    return True


def validate_api_key(key: str) -> bool | str:
    """Validate API key format.

    Args:
        key: API key to validate.

    Returns:
        True if valid, error message string otherwise.
    """
    if not key:
        return True  # Empty is allowed (use env var)

    if len(key) < 10:
        return "API key seems too short"

    return True


def validate_budget(value: str) -> bool | str:
    """Validate budget value.

    Args:
        value: Budget value string.

    Returns:
        True if valid, error message string otherwise.
    """
    if not value:
        return True  # Empty is allowed

    try:
        budget = float(value)
        if budget < 0:
            return "Budget must be positive"
        return True
    except ValueError:
        return "Invalid number format"


def validate_date(date_str: str) -> bool | str:
    """Validate date format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate.

    Returns:
        True if valid, error message string otherwise.
    """
    if not date_str:
        return True  # Empty is allowed

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return "Date must be in YYYY-MM-DD format"

    return True
