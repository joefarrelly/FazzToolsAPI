"""Tests for keybind helper functions.

Covers getKeybindMap dispatch and _build_single_keybinds transformation logic.
No DB access needed — these are pure functions.
"""

from apicore.libs.keybind_builder import build_single_keybinds
from apicore.libs.keybind_mapping import MAPPING_DEFAULT, MAPPING_DOMINOS, getKeybindMap

# ---------------------------------------------------------------------------
# getKeybindMap
# ---------------------------------------------------------------------------


class TestGetKeybindMap:
    def test_dominos_returns_dominos_mapping(self):
        assert getKeybindMap("Dominos") is MAPPING_DOMINOS

    def test_unknown_addon_returns_default(self):
        assert getKeybindMap("SomeUnknownAddon") is MAPPING_DEFAULT

    def test_empty_string_returns_default(self):
        assert getKeybindMap("") is MAPPING_DEFAULT

    def test_bartender_returns_none(self):
        # Bartender mapping is not yet implemented — documents the current gap
        assert getKeybindMap("Bartender") is None

    def test_default_mapping_slot1_is_actionbutton1(self):
        assert MAPPING_DEFAULT[1] == "ACTIONBUTTON1"

    def test_dominos_slot13_is_dominos_button(self):
        # Dominos re-maps slots 13+ to its own button names
        assert MAPPING_DOMINOS[13] == "CLICK DominosActionButton1:HOTKEY"


# ---------------------------------------------------------------------------
# _build_single_keybinds
# ---------------------------------------------------------------------------

# Minimal data structure matching what the Lua parser produces for a single alt
_BASE_ALT_CONFIG = {
    "kbConfig": {
        "addon": "Default",
        "map": {
            "ACTIONBUTTON1": "1",
            "ACTIONBUTTON2": "2",
            "ACTIONBUTTON3": "E",
        },
    },
    "kb": {
        "Frost": {
            "1": "spell:100",
            "2": "spell:200",
            "3": "spell:300",
        }
    },
    "spell": {
        "Frost": {
            "Base": {
                "100": ["Frostbolt"],
                "200": ["Ice Lance", "spell_frost_frostlance"],
                "300": ["Glacial Spike"],
            }
        }
    },
}

_DATA = {"alts": {"Mage-Realm": _BASE_ALT_CONFIG}}


class TestBuildSingleKeybinds:
    def _build(self, data=None, alt="Mage", realm="Realm", spec="Frost"):
        return build_single_keybinds(data or _DATA, alt, realm, spec)

    def test_returns_list_of_sections(self):
        result = self._build()
        assert isinstance(result, list)
        assert all(isinstance(s, list) and len(s) == 2 for s in result)

    def test_bound_spell_has_correct_keybind(self):
        result = self._build()
        base_section = next(s for s in result if s[0] == "Base")
        spells_by_name = {entry[0]: entry for entry in base_section[1]}
        assert spells_by_name["Frostbolt"][-1] == "1"
        assert spells_by_name["Ice Lance"][-1] == "2"

    def test_spell_with_icon_includes_icon(self):
        result = self._build()
        base_section = next(s for s in result if s[0] == "Base")
        spells_by_name = {entry[0]: entry for entry in base_section[1]}
        # Ice Lance has icon data in spell_info
        assert spells_by_name["Ice Lance"][1] == "spell_frost_frostlance"

    def test_unbound_slot_shows_unbound(self):
        data = {
            "alts": {
                "Mage-Realm": {
                    **_BASE_ALT_CONFIG,
                    "kb": {"Frost": {}},  # no keybinds assigned
                }
            }
        }
        result = build_single_keybinds(data, "Mage", "Realm", "Frost")
        base_section = next(s for s in result if s[0] == "Base")
        assert all(entry[-1] == "UNBOUND" for entry in base_section[1])

    def test_spells_sorted_alphabetically_within_section(self):
        result = self._build()
        base_section = next(s for s in result if s[0] == "Base")
        names = [entry[0] for entry in base_section[1]]
        assert names == sorted(names)

    def test_misc_section_always_present(self):
        result = self._build()
        section_names = [s[0] for s in result]
        assert "Misc" in section_names

    def test_item_binding_appears_in_misc(self):
        data = {
            "alts": {
                "Mage-Realm": {
                    **_BASE_ALT_CONFIG,
                    "kb": {"Frost": {"1": "item:Hearthstone"}},
                    "spell": {"Frost": {}},
                    "item": {"Hearthstone": ["Hearthstone", 6948, "Consumable"]},
                }
            }
        }
        result = build_single_keybinds(data, "Mage", "Realm", "Frost")
        misc_section = next(s for s in result if s[0] == "Misc")
        misc_names = [entry[0] for entry in misc_section[1]]
        assert "Hearthstone" in misc_names

    def test_missing_slot_in_keybind_map_is_silently_skipped(self):
        data = {
            "alts": {
                "Mage-Realm": {
                    **_BASE_ALT_CONFIG,
                    "kb": {"Frost": {"999": "spell:100"}},  # slot 999 not in mapping
                }
            }
        }
        result = build_single_keybinds(data, "Mage", "Realm", "Frost")
        base_section = next(s for s in result if s[0] == "Base")
        # Frostbolt should still appear, but as UNBOUND since slot couldn't be mapped
        names = [entry[0] for entry in base_section[1]]
        assert "Frostbolt" in names
        frostbolt = next(e for e in base_section[1] if e[0] == "Frostbolt")
        assert frostbolt[-1] == "UNBOUND"
