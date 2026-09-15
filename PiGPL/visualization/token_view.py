"""
visualization/token_view.py
=============================
Purpose:
    Convert the list[Token] produced by compiler/lexer.py into a
    JSON-serializable table (Lexeme | Token Type | Line | Column) for the
    UI, and persist it to outputs/tokens/tokens.json as an exportable
    artifact.

Input:
    tokens: list[compiler.lexer.Token]

Output:
    list[dict] with keys: lexeme, type, line, column (also written to
    outputs/tokens/tokens.json)
"""

import json
import os


def tokens_to_table(tokens):
    return [
        {
            "lexeme": str(t.value),
            "type": t.type,
            "line": t.line,
            "column": t.column,
        }
        for t in tokens
    ]


def save_tokens_json(tokens, output_dir="outputs/tokens"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "tokens.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tokens_to_table(tokens), f, indent=2)
    return path
