from __future__ import annotations


def snake_to_lower_camel(name: str) -> str:
    """
    Convert snake_case to lowerCamelCase.

    Rules:
    - deterministic
    - ASCII-only
    - no leading/trailing underscores
    - no abbreviation expansion
    - reversible by convention

    Examples:
        base_url -> baseUrl
        api_version -> apiVersion
        is_consumable -> isConsumable
    """
    if "_" not in name:
        return name

    parts = name.split("_")

    if not parts or any(not part for part in parts):
        raise ValueError(f"Invalid snake_case identifier: {name!r}")

    return parts[0] + "".join(part.capitalize() for part in parts[1:])
