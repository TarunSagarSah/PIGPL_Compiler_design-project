"""
visualization package
======================
Purpose:
    Turns raw compiler-stage data (tokens, AST, symbol table, pipeline
    status) into visual artifacts: tables (JSON, for the UI), and PNG
    images (tree diagrams, pipeline diagrams) saved under outputs/.

    This layer never changes compiler semantics -- it only observes and
    renders the outputs already produced by compiler/*. This mirrors the
    "Visualization Layer" module described in the Phase 1 system design
    (Section 8.3): "presents phase outputs and diagnostics without
    changing compiler semantics."
"""
