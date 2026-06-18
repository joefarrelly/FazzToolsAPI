"""Pure keybind-building logic, extracted from views.py.

These functions transform a parsed Lua addon dict into the response shapes
consumed by the frontend. No Django models are touched here except for
_build_all_keybinds, which looks up ProfileAlt for class display names.
"""

import logging

from apicore.libs.keybind_mapping import getKeybindMap

logger = logging.getLogger(__name__)

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

_SPAM_FILTER = {
    "Auto Attack",
    "Mobile Banking",
    "Revive Battle Pets",
    "Vindicaar Matrix Crystal",
    "Shoot",
}

_SECTION_ORDER = {"Base": 0, "Talent": 1, "Misc": 2}


def tier_sort_key(tier_name: str) -> int:
    name_lower = tier_name.lower()
    for keyword, order in _EXPANSION_ORDER.items():
        if keyword in name_lower:
            return order
    return 999


def build_all_keybinds(data: dict, user_id: str) -> list:
    from apicore.models import ProfileAlt

    result = []
    for alt_key, alt_config in data.get("alts", {}).items():
        specs = []
        try:
            if alt_config.get("kb") is not None:
                specs = list(alt_config["kb"].keys())
            else:
                specs = ["---", "---", "---", "---"]
        except (KeyError, TypeError):
            specs = ["---", "---", "---", "---"]

        specs.sort()
        while len(specs) < 4:
            specs.append("---")

        name, realm = (alt_key.split("-", 1) + [""])[:2]
        try:
            alt_obj = ProfileAlt.objects.get(alt_name=name, alt_realm=realm)
            row = [name, realm, alt_obj.get_alt_class_display()] + specs
            result.append(row)
        except ProfileAlt.DoesNotExist:
            logger.debug("Alt not in DB: %s", alt_key)

    result.sort(key=lambda x: (x[1], x[0]))
    return result


def build_single_keybinds(data: dict, alt: str, realm: str, spec: str) -> list:
    alt_key = f"{alt}-{realm}"
    alt_config = data["alts"][alt_key]
    keybind_map = getKeybindMap(alt_config["kbConfig"]["addon"])

    user_keybind: dict[str, str] = {}
    for slot, nice_spell in alt_config["kb"][spec].items():
        prefix = nice_spell.split(":")[0]

        if prefix == "spell":
            try:
                user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
            except (KeyError, ValueError):
                pass

        elif prefix == "macro":
            macro_name = nice_spell.split(":")[1]
            found = False
            for tab in alt_config.get("spell", {}).get(spec, {}):
                for spell_id, spell_info in alt_config["spell"][spec][tab].items():
                    if spell_info[0] in alt_config["macro"][macro_name][2]:
                        found = True
                        spell_key = f"spell:{spell_id}"
                        try:
                            bound = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                        except (KeyError, ValueError):
                            continue
                        if spell_key not in user_keybind:
                            user_keybind[spell_key] = bound
                        elif user_keybind[spell_key] != bound:
                            user_keybind[spell_key] += f" | {bound}"
            if not found:
                try:
                    user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                except (KeyError, ValueError):
                    pass

        elif prefix == "item":
            item_name = nice_spell.split(":")[1]
            if item_name in alt_config.get("item", {}):
                try:
                    user_keybind[nice_spell] = alt_config["kbConfig"]["map"][keybind_map[int(slot)]]
                except (KeyError, ValueError):
                    pass

    full_result = []
    for tab in alt_config.get("spell", {}).get(spec, {}):
        spells = []
        for spell_id, spell_info in alt_config["spell"][spec][tab].items():
            if spell_info[0] in _SPAM_FILTER:
                continue
            entry = [spell_info[0]]
            if len(spell_info) > 1:
                entry.append(spell_info[1])
            entry.append(user_keybind.get(f"spell:{spell_id}", "UNBOUND"))
            spells.append(entry)
        spells.sort(key=lambda x: x[0])
        full_result.append([tab.title(), spells])

    misc = []
    for item_name, item_info in alt_config.get("item", {}).items():
        if f"item:{item_name}" in user_keybind:
            misc.append([item_info[0], user_keybind[f"item:{item_name}"]])
    for macro_name, macro_info in alt_config.get("macro", {}).items():
        if f"macro:{macro_name}" in user_keybind:
            misc.append([f"[Macro] {macro_info[0]}", user_keybind[f"macro:{macro_name}"]])
    misc.sort(key=lambda x: x[0])
    full_result.append(["Misc", misc])

    full_result.sort(key=lambda x: _SECTION_ORDER.get(x[0], 99))

    if len(full_result) >= 2:
        full_result[0][1] = [x for x in full_result[0][1] if x not in full_result[1][1]]

    return full_result
