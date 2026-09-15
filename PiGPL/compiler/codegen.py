"""
compiler/codegen.py
=====================
STATUS: Planned for Phase 3. Not implemented.

Purpose (per the Phase 1 system design):
    Translate optimized IR into a selected target-level representation
    (the Phase 1 document leaves the exact target undecided: "assembly-like
    code, bytecode, LLVM IR, or another suitable target representation" --
    Section 9.1), then execute it and produce the final program output.

Planned interface:

    def generate_target(optimized_ir) -> TargetProgram
    def execute(target_program) -> ExecutionResult

Design consideration carried over from the Phase 1 document (Section 7.4):
target generation is intentionally left open in Phase 1 so the final choice
can be made after evaluating implementation effort and educational value.
"""

PHASE = "Planned for Phase 3"


def generate_target(optimized_ir):
    """Placeholder. Will produce the selected target-level representation
    once implemented in Phase 3."""
    raise NotImplementedError("Target code generation is planned for Phase 3.")


def execute(target_program):
    """Placeholder. Will run the target representation and return the
    program's final output once implemented in Phase 3."""
    raise NotImplementedError("Execution is planned for Phase 3.")
