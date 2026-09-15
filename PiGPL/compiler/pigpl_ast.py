"""
compiler/pigpl_ast.py
======================
Purpose:
    Defines the Abstract Syntax Tree (AST) node classes produced by the
    PiGPL parser. Named `pigpl_ast.py` (not `ast.py`) to avoid clashing with
    Python's own standard-library `ast` module.

Input:
    Constructed by compiler/parser.py while it reduces PiGPL grammar
    productions.

Output:
    A tree of ASTNode objects rooted at a `Program` node. The tree is
    consumed by compiler/semantic.py and visualization/ast_visualizer.py.

Design notes:
    Each node type mirrors a production in the PiGPL grammar (see the
    Phase 1 design document, Section 6.1). Every node stores `line`/`column`
    so later phases (and error messages) can always point back to the
    original source location.
"""


class ASTNode:
    """Base class for every PiGPL AST node."""

    def __init__(self, line=0, column=0):
        self.line = line
        self.column = column

    def label(self):
        """Short human-readable label used by the tree visualizer."""
        return type(self).__name__

    def children(self):
        """List of child ASTNode objects. Overridden by subclasses."""
        return []

    def to_dict(self):
        return {
            "label": self.label(),
            "line": self.line,
            "column": self.column,
            "children": [c.to_dict() for c in self.children()],
        }


class Program(ASTNode):
    def __init__(self, statements, line=0, column=0):
        super().__init__(line, column)
        self.statements = statements

    def label(self):
        return "Program"

    def children(self):
        return self.statements


class Declaration(ASTNode):
    """let <name>: <type> = <expr>"""

    def __init__(self, name, var_type, value, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.var_type = var_type
        self.value = value

    def label(self):
        return f"Declaration: {self.name} : {self.var_type}"

    def children(self):
        return [self.value]


class Assignment(ASTNode):
    """<name> = <expr>"""

    def __init__(self, name, value, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.value = value

    def label(self):
        return f"Assignment: {self.name}"

    def children(self):
        return [self.value]


class PrintStatement(ASTNode):
    def __init__(self, expression, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression

    def label(self):
        return "PrintStatement"

    def children(self):
        return [self.expression]


class IfStatement(ASTNode):
    def __init__(self, condition, then_block, else_block=None, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.then_block = then_block   # list[ASTNode]
        self.else_block = else_block   # list[ASTNode] or None

    def label(self):
        return "IfStatement"

    def children(self):
        kids = [ConditionWrapper(self.condition), BlockWrapper("Then", self.then_block)]
        if self.else_block is not None:
            kids.append(BlockWrapper("Else", self.else_block))
        return kids


class ConditionWrapper(ASTNode):
    """Presentation-only wrapper so the tree view has a clear 'Condition' node."""

    def __init__(self, condition):
        super().__init__(condition.line, condition.column)
        self.condition = condition

    def label(self):
        return "Condition"

    def children(self):
        return [self.condition]


class BlockWrapper(ASTNode):
    """Presentation-only wrapper so the tree view groups a block's statements."""

    def __init__(self, name, statements):
        super().__init__()
        self.name = name
        self.statements = statements

    def label(self):
        return f"Body ({self.name})"

    def children(self):
        return self.statements


class BinaryOp(ASTNode):
    def __init__(self, operator, left, right, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator
        self.left = left
        self.right = right

    def label(self):
        return f"BinaryOp: {self.operator}"

    def children(self):
        return [self.left, self.right]


class UnaryOp(ASTNode):
    def __init__(self, operator, operand, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand

    def label(self):
        return f"UnaryOp: {self.operator}"

    def children(self):
        return [self.operand]


class Identifier(ASTNode):
    def __init__(self, name, line=0, column=0):
        super().__init__(line, column)
        self.name = name

    def label(self):
        return f"Identifier: {self.name}"


class Literal(ASTNode):
    def __init__(self, value, literal_type, line=0, column=0):
        super().__init__(line, column)
        self.value = value
        self.literal_type = literal_type

    def label(self):
        return f"{self.literal_type.capitalize()}: {self.value}"


class PrintCall(ASTNode):
    """print(...) used as an expression statement (kept distinct from
    PrintStatement for grammar clarity if extended later)."""

    def __init__(self, argument, line=0, column=0):
        super().__init__(line, column)
        self.argument = argument

    def label(self):
        return "Print"

    def children(self):
        return [self.argument]
