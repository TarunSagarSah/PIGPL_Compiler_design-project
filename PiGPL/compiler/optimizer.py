"""
compiler/optimizer.py
=======================
STATUS: Planned for Phase 3. Not implemented.

Purpose (per the Phase 1 system design):
    Apply basic, semantics-preserving optimizations to the IR produced by
    compiler/ir.py -- e.g. constant folding, as called out explicitly in
    the Phase 1 design document's Expected Outcomes and Methodology
    sections.

Planned interface:

    def optimize(ir_instructions) -> list[IRInstruction]

Planned first optimization: constant folding (evaluate expressions whose
operands are already known constants at compile time, e.g. `t1 = 2 + 3`
becomes `t1 = 5`), because it is the optimization explicitly named in the
Phase 1 design document and is straightforward to demonstrate visually
(show IR before and after).
"""

PHASE = "Planned for Phase 3"


def optimize(ir_instructions):
    """Placeholder. Will apply constant folding and similar local
    optimizations once implemented in Phase 3."""
    raise NotImplementedError("IR optimization is planned for Phase 3.")
