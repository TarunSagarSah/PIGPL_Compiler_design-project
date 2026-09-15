"""
compiler/ir.py
================
STATUS: Planned for Phase 2. Not implemented.

Purpose (per the Phase 1 system design):
    Translate a semantically-validated AST into an intermediate
    representation, specifically three-address-code-style instructions
    (e.g. `t1 = x + y`), as described in Section 8.3 of the Phase 1 design
    document ("IR Generator: translates semantically valid structures into
    an intermediate representation").

Planned interface (stable now so Phase 2 can implement it without changing
callers in app.py):

    def generate(program_ast, symbol_table) -> list[IRInstruction]

Planned data structure:
    A flat list of IRInstruction(op, arg1, arg2, result) tuples/records,
    one per elementary operation (matching the classic three-address-code
    model from Aho/Sethi/Ullman, Chapter 6).

This module intentionally contains no executable compiler logic yet -- see
the project README's "Phase 2 Plan" section for the implementation plan.
"""

PHASE = "Planned for Phase 2"


def generate(program_ast, symbol_table):
    """
    Placeholder. Will translate `program_ast` into three-address code once
    implemented in Phase 2.
    """
    raise NotImplementedError("Intermediate code generation is planned for Phase 2.")
