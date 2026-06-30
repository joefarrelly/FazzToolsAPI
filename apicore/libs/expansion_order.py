_EXPANSION_ORDER: dict[str, int] = {
    "classic": 0,
    "outland": 1,
    "northrend": 2,
    "cataclysm": 3,
    "pandaria": 4,
    "draenor": 5,
    "legion": 6,
    "kul tiran": 7,
    "zandalari": 7,
    "shadowlands": 8,
    "dragon isles": 9,
    "khaz algar": 10,
    "midnight": 11,
}


def tier_sort_key(tier_name: str) -> int:
    name_lower = tier_name.lower()
    for keyword, order in _EXPANSION_ORDER.items():
        if keyword in name_lower:
            return order
    return 999
