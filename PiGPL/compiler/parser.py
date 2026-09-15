"""
compiler/parser.py
===================
Purpose:
    The Syntax Analyzer for PiGPL. Consumes the token stream produced by
    compiler/lexer.py, validates it against the PiGPL grammar, and builds
    an Abstract Syntax Tree (AST) using the node classes in
    compiler/pigpl_ast.py.

Input:
    PiGPL source code (string). Internally re-tokenizes using compiler.lexer
    so PLY's yacc module (which pulls tokens lazily) always sees a fresh
    lexer state.

Output:
    (ast_root, errors)
    ast_root -> pigpl_ast.Program, or None if parsing failed completely
    errors   -> list[SyntaxErrorPiGPL]

Grammar implemented in Phase 1 (a deliberately small, reliable subset of
the full PiGPL grammar defined in the Phase 1 design document):

    program     ::= statement*
    statement   ::= declaration | assignment | if_stmt | print_stmt
    declaration ::= "let" IDENTIFIER ":" type "=" expression
    assignment  ::= IDENTIFIER "=" expression
    print_stmt  ::= "print" "(" expression ")"
    if_stmt     ::= "if" expression block ("else" block)?
    block       ::= "{" statement* "}"
    expression  ::= comparison
    comparison  ::= term (("=="|"!="|"<"|">"|"<="|">=") term)*
    term        ::= factor (("+"|"-") factor)*
    factor      ::= unary (("*"|"/"|"%") unary)*
    unary       ::= "-" unary | primary
    primary     ::= INTEGER | FLOATNUM | STRING | "true" | "false"
                  | IDENTIFIER | "(" expression ")"
    type        ::= "int" | "float" | "bool" | "string"

Full-language productions from the Phase 1 grammar (elif/for/while/in,
functions, lists, logical and/or/not, function calls) are intentionally
NOT implemented yet. They are listed here, and in the README's Phase 2
plan, as the next grammar productions to add -- the parser architecture
(PLY yacc + this module) does not need to change to add them, only new
grammar rule functions need to be written.

Important algorithm:
    PLY's `yacc` builds an LALR(1) parser from the `p_*` grammar-rule
    functions below (an automatically generated shift-reduce parser),
    which is the standard bottom-up parsing technique taught for syntax
    analysis.
"""

import ply.yacc as yacc

from compiler.lexer import tokens, build_lexer  # noqa: F401  (tokens required by PLY)
from compiler.errors import SyntaxErrorPiGPL
from compiler import pigpl_ast as ast


# ---------------------------------------------------------------------------
# Operator precedence (lowest to highest). Mirrors the grammar hierarchy:
# comparison < term(+ -) < factor(* / %) < unary(-)
# ---------------------------------------------------------------------------
precedence = (
    ("left", "EQ", "NEQ", "LT", "GT", "LE", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)

_current_errors = []


def _pos(p, i):
    return p.lineno(i), 1  # PLY yacc tracks line numbers well; column is
    # not separately tracked by yacc, so statement-level nodes report the
    # line only (sufficient for teacher-facing diagnostics in Phase 1).


# ---------------------------------------------------------------------------
# Program / statement list
# ---------------------------------------------------------------------------
def p_program(p):
    "program : statement_list"
    p[0] = ast.Program(p[1], line=1)


def p_statement_list_multi(p):
    "statement_list : statement_list statement"
    p[0] = p[1] + [p[2]]


def p_statement_list_single(p):
    "statement_list : statement"
    p[0] = [p[1]]


def p_statement(p):
    """statement : declaration
    | assignment
    | print_stmt
    | if_stmt"""
    p[0] = p[1]


# ---------------------------------------------------------------------------
# Declaration:  let x : int = 10
# ---------------------------------------------------------------------------
def p_declaration(p):
    "declaration : LET IDENTIFIER COLON TYPE ASSIGN expression"
    p[0] = ast.Declaration(p[2], p[4], p[6], line=p.lineno(1), column=1)


# ---------------------------------------------------------------------------
# Assignment:  x = expr
# ---------------------------------------------------------------------------
def p_assignment(p):
    "assignment : IDENTIFIER ASSIGN expression"
    p[0] = ast.Assignment(p[1], p[3], line=p.lineno(1), column=1)


# ---------------------------------------------------------------------------
# print(expr)
# ---------------------------------------------------------------------------
def p_print_stmt(p):
    "print_stmt : PRINT LPAREN expression RPAREN"
    p[0] = ast.PrintStatement(p[3], line=p.lineno(1), column=1)


# ---------------------------------------------------------------------------
# if expression block (else block)?
# ---------------------------------------------------------------------------
def p_if_stmt_no_else(p):
    "if_stmt : IF expression block"
    p[0] = ast.IfStatement(p[2], p[3], None, line=p.lineno(1), column=1)


def p_if_stmt_else(p):
    "if_stmt : IF expression block ELSE block"
    p[0] = ast.IfStatement(p[2], p[3], p[5], line=p.lineno(1), column=1)


def p_block(p):
    "block : LBRACE statement_list RBRACE"
    p[0] = p[2]


def p_block_empty(p):
    "block : LBRACE RBRACE"
    p[0] = []


# ---------------------------------------------------------------------------
# Expressions (comparison -> term -> factor -> unary -> primary)
# ---------------------------------------------------------------------------
def p_expression_comparison(p):
    """expression : expression EQ term
    | expression NEQ term
    | expression LT term
    | expression GT term
    | expression LE term
    | expression GE term"""
    p[0] = ast.BinaryOp(p[2], p[1], p[3], line=p.lineno(2), column=1)


def p_expression_term(p):
    "expression : term"
    p[0] = p[1]


def p_term_binop(p):
    """term : term PLUS factor
    | term MINUS factor"""
    p[0] = ast.BinaryOp(p[2], p[1], p[3], line=p.lineno(2), column=1)


def p_term_factor(p):
    "term : factor"
    p[0] = p[1]


def p_factor_binop(p):
    """factor : factor TIMES unary
    | factor DIVIDE unary
    | factor MODULO unary"""
    p[0] = ast.BinaryOp(p[2], p[1], p[3], line=p.lineno(2), column=1)


def p_factor_unary(p):
    "factor : unary"
    p[0] = p[1]


def p_unary_minus(p):
    "unary : MINUS unary %prec UMINUS"
    p[0] = ast.UnaryOp("-", p[2], line=p.lineno(1), column=1)


def p_unary_primary(p):
    "unary : primary"
    p[0] = p[1]


def p_primary_group(p):
    "primary : LPAREN expression RPAREN"
    p[0] = p[2]


def p_primary_integer(p):
    "primary : INTEGER"
    p[0] = ast.Literal(p[1], "int", line=p.lineno(1), column=1)


def p_primary_float(p):
    "primary : FLOATNUM"
    p[0] = ast.Literal(p[1], "float", line=p.lineno(1), column=1)


def p_primary_string(p):
    "primary : STRING"
    p[0] = ast.Literal(p[1], "string", line=p.lineno(1), column=1)


def p_primary_true(p):
    "primary : TRUE"
    p[0] = ast.Literal(True, "bool", line=p.lineno(1), column=1)


def p_primary_false(p):
    "primary : FALSE"
    p[0] = ast.Literal(False, "bool", line=p.lineno(1), column=1)


def p_primary_identifier(p):
    "primary : IDENTIFIER"
    p[0] = ast.Identifier(p[1], line=p.lineno(1), column=1)


# ---------------------------------------------------------------------------
# Error recovery
# ---------------------------------------------------------------------------
def p_error(p):
    if p is None:
        _current_errors.append(
            SyntaxErrorPiGPL("Unexpected end of input; a statement or expression was incomplete.")
        )
    else:
        _current_errors.append(
            SyntaxErrorPiGPL(
                f"Unexpected token '{p.value}' ({p.type})",
                line=p.lineno,
                column=1,
            )
        )


_parser = None


def _get_parser():
    global _parser
    if _parser is None:
        _parser = yacc.yacc(debug=False, write_tables=False)
    return _parser


def parse(source_code):
    """
    Parse PiGPL `source_code` into an AST.

    Returns:
        (ast_root, errors)
        ast_root: pigpl_ast.Program, or None if nothing could be parsed
        errors: list[SyntaxErrorPiGPL]
    """
    _current_errors.clear()
    lexer = build_lexer()
    parser = _get_parser()
    try:
        result = parser.parse(source_code, lexer=lexer)
    except Exception as exc:  # pragma: no cover - defensive guard for viva demos
        _current_errors.append(SyntaxErrorPiGPL(f"Parser failure: {exc}"))
        result = None
    return result, list(_current_errors)
