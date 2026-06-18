"""Tests for apicore.libs.lua_parser.LuaParser.

The parser skips lines[0] and lines[1] (the SavedVariables preamble and
outer opening brace) and reads from lines[2] onwards.
"""

from apicore.libs.lua_parser import LuaParser


def _make_lines(*content_lines: str) -> list[str]:
    """Wrap content lines with the standard preamble the parser skips."""
    return ["FazzToolsScraperDB = {\n", "preamble\n", *content_lines]


class TestFlatDict:
    def test_single_string_value(self):
        lines = _make_lines('["key"] = "value",\n', "}\n")
        assert LuaParser(lines).parse() == {"key": "value"}

    def test_multiple_keys(self):
        lines = _make_lines(
            '["a"] = "1",\n',
            '["b"] = "2",\n',
            "}\n",
        )
        assert LuaParser(lines).parse() == {"a": "1", "b": "2"}

    def test_numeric_key_gets_quoted(self):
        # Keys without leading '"' are wrapped in quotes so JSON accepts them
        lines = _make_lines('[1] = "val",\n', "}\n")
        assert LuaParser(lines).parse() == {"1": "val"}

    def test_inline_comment_stripped(self):
        lines = _make_lines('"item1", -- [1]\n', "}\n")
        result = LuaParser(lines).parse()
        assert result == ["item1"]


class TestNestedDict:
    def test_nested_one_level(self):
        lines = _make_lines(
            '["outer"] = {\n',
            '["inner"] = "val",\n',
            "},\n",
            "}\n",
        )
        assert LuaParser(lines).parse() == {"outer": {"inner": "val"}}

    def test_empty_nested_table_omitted(self):
        lines = _make_lines(
            '["key"] = {\n',
            "},\n",
            "}\n",
        )
        # An empty child list produces "[]", which is skipped
        assert LuaParser(lines).parse() == {}

    def test_deeply_nested(self):
        lines = _make_lines(
            '["l1"] = {\n',
            '["l2"] = {\n',
            '["l3"] = "deep",\n',
            "},\n",
            "},\n",
            "}\n",
        )
        assert LuaParser(lines).parse() == {"l1": {"l2": {"l3": "deep"}}}


class TestListStructure:
    def test_bare_string_values(self):
        lines = _make_lines('"alpha",\n', '"beta",\n', "}\n")
        assert LuaParser(lines).parse() == ["alpha", "beta"]


class TestNilHandling:
    def test_nil_becomes_empty_string(self):
        lines = _make_lines("nil,\n", "}\n")
        result = LuaParser(lines).parse()
        assert result == [""]

    def test_nil_inside_string_untouched(self):
        # The word "nil" inside a quoted string (the preceding char is '"')
        # should not be replaced — e.g. '["k"] = "nil"'
        lines = _make_lines('["k"] = "nil",\n', "}\n")
        result = LuaParser(lines).parse()
        # Value is the literal string "nil", not replaced
        assert result == {"k": "nil"}


class TestRealWorldStructure:
    def test_alts_kb_structure(self):
        """Minimal representation of the actual FazzToolsScraper output."""
        lines = _make_lines(
            '["alts"] = {\n',
            '["Toon-Realm"] = {\n',
            '["kb"] = {\n',
            '["Base"] = {\n',
            '["1"] = "spell:100",\n',
            "},\n",  # closes Base
            "},\n",  # closes kb
            "},\n",  # closes Toon-Realm
            "},\n",  # closes alts
            "}\n",  # closes outer
        )
        result = LuaParser(lines).parse()
        assert result == {"alts": {"Toon-Realm": {"kb": {"Base": {"1": "spell:100"}}}}}
