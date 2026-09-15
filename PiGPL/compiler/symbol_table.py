"""
compiler/symbol_table.py
=========================
Purpose:
    Maintains identifier information (name, type, scope, value/attribute)
    discovered while the Semantic Analyzer walks the AST.

Input:
    `insert()` calls made by compiler/semantic.py as declarations are
    validated.

Output:
    A list of SymbolEntry rows, exposed to the UI as a table (Name, Type,
    Scope, Value/Attribute) exactly as specified in the Phase 1 design.

Data structure:
    A single flat table (list of SymbolEntry) tagged with a `scope` string
    per row. Phase 1 uses one scope, "global", because the implemented
    grammar subset has no functions yet. The `scope` field and the
    `enter_scope`/`exit_scope` methods already exist so Phase 2 (which
    adds functions and therefore nested scopes) can switch to a real
    scope stack without changing the SymbolTable's public interface.
"""

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class SymbolEntry:
    name: str
    var_type: str
    scope: str
    value: Any = None

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.var_type,
            "scope": self.scope,
            "value": self.value,
        }


class SymbolTable:
    def __init__(self):
        self._entries: List[SymbolEntry] = []
        self._scope_stack = ["global"]

    # -- scope management (Phase 1 uses only "global"; ready for Phase 2) --
    def current_scope(self):
        return self._scope_stack[-1]

    def enter_scope(self, name):
        self._scope_stack.append(name)

    def exit_scope(self):
        if len(self._scope_stack) > 1:
            self._scope_stack.pop()

    # -- entry management --
    def declare(self, name, var_type, value=None):
        entry = SymbolEntry(name=name, var_type=var_type, scope=self.current_scope(), value=value)
        self._entries.append(entry)
        return entry

    def lookup(self, name):
        """Look up `name` starting from the innermost currently-tracked scope."""
        for entry in reversed(self._entries):
            if entry.name == name and entry.scope == self.current_scope():
                return entry
        # Phase 1 has only the global scope, so a simple fallback search
        # covers it; Phase 2 will walk the enclosing scope chain here.
        for entry in reversed(self._entries):
            if entry.name == name:
                return entry
        return None

    def is_declared(self, name):
        return self.lookup(name) is not None

    def update_value(self, name, value):
        entry = self.lookup(name)
        if entry:
            entry.value = value

    def all_entries(self):
        return list(self._entries)

    def to_list(self):
        return [e.to_dict() for e in self._entries]
