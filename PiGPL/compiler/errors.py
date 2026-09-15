"""
compiler/errors.py
===================
Purpose:
    Defines a single, uniform error representation used by every compiler
    phase (lexical, syntax, semantic, and — in later phases — runtime).

Why a shared error type:
    A teacher/viva reviewer should be able to look at ANY error, from ANY
    phase, and immediately see which phase raised it, where in the source
    it happened, and what the problem was. Using one class for all phases
    keeps the error-reporting format consistent across the whole pipeline.

Data carried by every error:
    phase   -> which compiler phase raised it ("Lexical", "Syntax", "Semantic", ...)
    message -> human readable explanation
    line    -> 1-based line number in the source (0 if unknown)
    column  -> 1-based column number in the source (0 if unknown)
"""

from dataclasses import dataclass


@dataclass
class CompilerError:
    """A single diagnostic produced by some phase of the PiGPL compiler."""
    phase: str
    message: str
    line: int = 0
    column: int = 0

    def to_dict(self):
        return {
            "phase": self.phase,
            "message": self.message,
            "line": self.line,
            "column": self.column,
        }

    def __str__(self):
        loc = f"line {self.line}, column {self.column}" if self.line else "unknown location"
        return f"[{self.phase} Error] {self.message} ({loc})"


class LexicalError(CompilerError):
    def __init__(self, message, line=0, column=0):
        super().__init__(phase="Lexical", message=message, line=line, column=column)


class SyntaxErrorPiGPL(CompilerError):
    def __init__(self, message, line=0, column=0):
        super().__init__(phase="Syntax", message=message, line=line, column=column)


class SemanticError(CompilerError):
    def __init__(self, message, line=0, column=0):
        super().__init__(phase="Semantic", message=message, line=line, column=column)


class ErrorReport:
    """
    Collects CompilerError objects produced across all phases of a single
    compilation run so the UI can show them together, grouped by phase.
    """

    def __init__(self):
        self.errors = []

    def add(self, error: CompilerError):
        self.errors.append(error)

    def has_errors(self):
        return len(self.errors) > 0

    def by_phase(self):
        grouped = {}
        for err in self.errors:
            grouped.setdefault(err.phase, []).append(err)
        return grouped

    def to_list(self):
        return [e.to_dict() for e in self.errors]
