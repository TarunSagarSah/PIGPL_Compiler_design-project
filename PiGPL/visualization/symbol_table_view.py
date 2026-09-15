"""
visualization/symbol_table_view.py
=====================================
Purpose:
    Convert compiler.symbol_table.SymbolTable into a JSON-serializable
    table (Name | Type | Scope | Value/Attribute) for the UI, and persist
    it to outputs/symbol_table/symbol_table.json as an exportable artifact.

Input:
    symbol_table: compiler.symbol_table.SymbolTable

Output:
    list[dict] with keys: name, type, scope, value (also written to
    outputs/symbol_table/symbol_table.json)
"""

import json
import os


def symbol_table_to_rows(symbol_table):
    return symbol_table.to_list()


def save_symbol_table_json(symbol_table, output_dir="outputs/symbol_table"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "symbol_table.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(symbol_table_to_rows(symbol_table), f, indent=2)
    return path
