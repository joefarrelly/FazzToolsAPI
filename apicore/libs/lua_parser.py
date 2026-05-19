import json
import re


class LuaParser:
    """Converts a FazzToolsScraper Lua addon export into a Python dict."""

    _LINE_RE = re.compile(r"^\s*(.*?),?(?: -- \[\d+\])?$")
    _KEY_VALUE_RE = re.compile(r"^\[(.*?)\] = (.*?)?$")

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.index = 1

    def parse(self) -> dict:
        _, json_str = self._recursive()
        return json.loads(json_str)

    def _recursive(self) -> tuple[str, str]:
        s_type = "list"
        result = []

        while self.index < len(self.lines):
            self.index += 1
            line_match = self._LINE_RE.search(self.lines[self.index])
            if not line_match:
                raise ValueError(
                    f"Unparseable Lua on line {self.index}: {self.lines[self.index]!r}"
                )

            token = line_match.group(1)

            if token == "{":
                child = self._recursive()
                if child[1] != "[]":
                    result.append(child[1])
                continue

            if token == "}":
                break

            kv_match = self._KEY_VALUE_RE.search(token)
            if kv_match:
                s_type = "dict"
                key = kv_match.group(1)
                value = kv_match.group(2)

                if key[0] != '"':
                    key = f'"{key}"'

                if value == "{":
                    child = self._recursive()
                    if child[1] != "[]":
                        result.append(f"{key}:{child[1]}")
                    continue

                if value == "}":
                    break

                result.append(f"{key}:{value}")
            else:
                nil_idx = token.find("nil")
                if nil_idx != -1 and token[nil_idx - 1] != '"':
                    token = token.replace("nil", '""')
                result.append(token)

        if s_type == "list":
            return ("list", "[{}]".format(",".join(result)))
        return ("dict", "{{{}}}".format(",".join(result)))
