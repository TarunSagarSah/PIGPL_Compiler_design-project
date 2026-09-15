"""
compiler/lexer.py
==================
Purpose:
    The Lexical Analyzer (scanner) for PiGPL. Converts raw PiGPL source text
    into a stream of classified Token objects, reporting lexical errors for
    characters that do not belong to any valid PiGPL token.

Input:
    A string containing PiGPL source code.

Output:
    (tokens, errors)
    tokens -> list[Token], one entry per recognized lexeme (in source order)
    errors -> list[LexicalError], one entry per invalid character encountered

Important data structures / algorithms:
    - Built on PLY (Python Lex-Yacc)'s `lex` module, which builds a
      Deterministic Finite Automaton (DFA) from the regular expressions
      declared below (`t_PLUS`, `t_ID`, function-based rules, etc.) and
      uses "maximal munch" (longest match) to tokenize the input, exactly
      like a hand-written DFA-based scanner would.
    - Keywords are recognized by first matching the general IDENTIFIER
      regular expression and then checking the matched lexeme against the
      `KEYWORDS` table. This is the standard technique used to avoid writing
      a separate regular expression per keyword.

Token categories implemented (per PiGPL Phase 1 language specification):
    KEYWORD, IDENTIFIER, INTEGER, FLOAT, STRING, BOOLEAN literal (true/false
    are tokenized as KEYWORD and interpreted as boolean literals by the
    parser), arithmetic/relational/logical operators, assignment, delimiters.

Note on scope:
    The PiGPL Phase 1 language specification defines a broader keyword set
    (elif, for, while, in, and, or, not, input) than the small statement
    subset implemented by the Phase 1 parser. The lexer recognizes the full
    keyword set now so that Phase 2/3 grammar extensions do not require any
    lexer changes -- only parser changes. This is intentional and documented
    in the README's Phase 2 plan.
"""

import ply.lex as lex
from compiler.errors import LexicalError

# ---------------------------------------------------------------------------
# Keyword table: lexeme -> token type
# ---------------------------------------------------------------------------
KEYWORDS = {
    "let": "LET",
    "int": "TYPE",
    "float": "TYPE",
    "bool": "TYPE",
    "string": "TYPE",
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "for": "FOR",
    "while": "WHILE",
    "in": "IN",
    "fn": "FN",
    "return": "RETURN",
    "print": "PRINT",
    "input": "INPUT",
    "true": "TRUE",
    "false": "FALSE",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
}

# ---------------------------------------------------------------------------
# Token list required by PLY. Includes keyword-derived token types plus the
# structural / literal / operator / delimiter tokens.
# ---------------------------------------------------------------------------
tokens = [
    "IDENTIFIER",
    "INTEGER",
    "FLOATNUM",
    "STRING",

    "PLUS", "MINUS", "TIMES", "DIVIDE", "MODULO",
    "ASSIGN",
    "EQ", "NEQ", "LT", "GT", "LE", "GE",
    "ARROW",

    "LPAREN", "RPAREN",
    "LBRACE", "RBRACE",
    "LBRACKET", "RBRACKET",
    "COMMA", "COLON",
] + sorted(set(KEYWORDS.values()))

# ---------------------------------------------------------------------------
# Simple, single-meaning operator/delimiter tokens (order matters: PLY sorts
# string-rules by regex length automatically, but multi-char operators such
# as "==" are still declared distinctly from "=" to keep the mapping clear).
# ---------------------------------------------------------------------------
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_MODULO = r"%"

t_EQ = r"=="
t_NEQ = r"!="
t_LE = r"<="
t_GE = r">="
t_ARROW = r"->"
t_LT = r"<"
t_GT = r">"
t_ASSIGN = r"="

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_COMMA = r","
t_COLON = r":"

t_ignore = " \t"  # spaces and tabs are skipped between tokens


def t_COMMENT(t):
    r"\#.*"
    pass  # comments produce no token; they are simply discarded


def t_FLOATNUM(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t


def t_INTEGER(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    t.value = t.value[1:-1]  # strip the surrounding quotes
    return t


def t_IDENTIFIER(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    t.type = KEYWORDS.get(t.value, "IDENTIFIER")
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


# Module-level buffer for lexical errors produced during the current
# tokenize() call. PLY requires t_error to be defined at module scope for
# the lexer's error dispatch table to pick it up when lex.lex() is built.
_current_source = [""]
_current_errors = []


def t_error(t):
    line_start = _current_source[0].rfind("\n", 0, t.lexpos) + 1
    column = (t.lexpos - line_start) + 1
    _current_errors.append(
        LexicalError(
            message=f"Invalid character '{t.value[0]}'",
            line=t.lineno,
            column=column,
        )
    )
    t.lexer.skip(1)


def find_column(source, token):
    line_start = source.rfind("\n", 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


class Token:
    """A single classified lexeme, used by the parser and visualization layer."""

    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "type": self.type,
            "lexeme": str(self.value),
            "line": self.line,
            "column": self.column,
        }

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.column})"


def build_lexer():
    return lex.lex()


def tokenize(source_code):
    """
    Run the PiGPL lexer over `source_code`.

    Returns:
        (tokens, errors)
        tokens: list[Token]
        errors: list[LexicalError]
    """
    lexer = build_lexer()
    _current_source[0] = source_code
    _current_errors.clear()
    lexer.input(source_code)

    tokens_out = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        col = find_column(source_code, tok)
        tokens_out.append(Token(tok.type, tok.value, tok.lineno, col))

    return tokens_out, list(_current_errors)
