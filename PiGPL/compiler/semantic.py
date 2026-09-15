"""
compiler/semantic.py
=====================
Purpose:
    The Semantic Analyzer for PiGPL. Walks the AST produced by
    compiler/parser.py and checks declarations, basic type compatibility,
    and identifier scope, populating the SymbolTable as it goes.

Input:
    ast_root: pigpl_ast.Program

Output:
    (symbol_table, checks, errors)
    symbol_table -> compiler.symbol_table.SymbolTable, filled with every
                    declared identifier
    checks       -> list[str] of human-readable ✓/✗ style results, used by
                    the UI's Semantic Analysis view
    errors       -> list[SemanticError]

Checks implemented in Phase 1 (matching the Phase 1 scope: declarations,
basic type checking, identifier-declared checks):
    - Redeclaration of an existing identifier in the same scope
    - Use of an undeclared identifier (in an expression, assignment, or
      print statement)
    - Basic type compatibility between a declared type and the type of the
      expression assigned to it (int/float numeric compatibility allowed;
      string/bool must match exactly)
    - Type compatibility for assignment to an existing variable
    - Condition of an `if` statement must evaluate to a boolean-producing
      expression (comparison) or boolean literal/identifier

Explicitly NOT implemented in Phase 1 (see README Phase 2 plan):
    - Function signature / parameter / return-type checking (no functions
      in the Phase 1 grammar subset yet)
    - Nested/function scope resolution (Phase 1 has only global scope)
    - List/array element type checking
"""

from compiler import pigpl_ast as ast
from compiler.errors import SemanticError
from compiler.symbol_table import SymbolTable

NUMERIC_TYPES = {"int", "float"}


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.checks = []  # human readable ✓ / ✗ lines for the UI

    # -- public entry point --------------------------------------------------
    def analyze(self, program: ast.Program):
        for stmt in program.statements:
            self._visit_statement(stmt)
        return self.symbol_table, self.checks, self.errors

    # -- statements ------------------------------------------------------------
    def _visit_statement(self, node):
        if isinstance(node, ast.Declaration):
            self._visit_declaration(node)
        elif isinstance(node, ast.Assignment):
            self._visit_assignment(node)
        elif isinstance(node, ast.PrintStatement):
            self._visit_print(node)
        elif isinstance(node, ast.IfStatement):
            self._visit_if(node)
        else:
            self._error(f"Unsupported statement type in Phase 1: {type(node).__name__}", node)

    def _visit_declaration(self, node: ast.Declaration):
        if self.symbol_table.is_declared(node.name):
            self._error(f"Identifier '{node.name}' is already declared", node)
            self._check(False, f"Redeclaration check for '{node.name}'")
            return

        value_type, value = self._visit_expression(node.value)
        self._check(True, f"Declaration valid: let {node.name} : {node.var_type}")

        if value_type is None:
            # An error already occurred while evaluating the expression;
            # still declare the symbol so later statements can reference it.
            self.symbol_table.declare(node.name, node.var_type, value)
            return

        if not self._types_compatible(node.var_type, value_type):
            self._error(
                f"Type mismatch in declaration of '{node.name}': expected {node.var_type}, found {value_type}",
                node,
            )
            self._check(False, f"Type valid for '{node.name}' ({node.var_type} = {value_type})")
        else:
            self._check(True, f"Type valid for '{node.name}' ({node.var_type})")

        self.symbol_table.declare(node.name, node.var_type, value)

    def _visit_assignment(self, node: ast.Assignment):
        entry = self.symbol_table.lookup(node.name)
        if entry is None:
            self._error(f"Undeclared identifier: {node.name}", node)
            self._check(False, f"Identifier declared: '{node.name}'")
            # Still evaluate the RHS so remaining diagnostics are useful.
            self._visit_expression(node.value)
            return

        self._check(True, f"Identifier declared: '{node.name}'")
        value_type, value = self._visit_expression(node.value)
        if value_type is not None and not self._types_compatible(entry.var_type, value_type):
            self._error(
                f"Type mismatch in assignment to '{node.name}': expected {entry.var_type}, found {value_type}",
                node,
            )
            self._check(False, f"Type valid for assignment to '{node.name}'")
        else:
            self._check(True, f"Type valid for assignment to '{node.name}'")
            self.symbol_table.update_value(node.name, value)

    def _visit_print(self, node: ast.PrintStatement):
        value_type, _ = self._visit_expression(node.expression)
        self._check(value_type is not None, "print() argument is a valid expression")

    def _visit_if(self, node: ast.IfStatement):
        cond_type, _ = self._visit_expression(node.condition)
        if cond_type is not None:
            self._check(True, "Condition is a valid expression")
        for stmt in node.then_block:
            self._visit_statement(stmt)
        if node.else_block:
            for stmt in node.else_block:
                self._visit_statement(stmt)

    # -- expressions -------------------------------------------------------
    def _visit_expression(self, node):
        """Returns (type_name, value) for `node`. type_name is None on error."""
        if isinstance(node, ast.Literal):
            return node.literal_type, node.value

        if isinstance(node, ast.Identifier):
            entry = self.symbol_table.lookup(node.name)
            if entry is None:
                self._error(f"Undeclared identifier: {node.name}", node)
                self._check(False, f"Identifier declared: '{node.name}'")
                return None, None
            self._check(True, f"Identifier declared: '{node.name}'")
            return entry.var_type, entry.value

        if isinstance(node, ast.UnaryOp):
            operand_type, operand_value = self._visit_expression(node.operand)
            if operand_type is None:
                return None, None
            if node.operator == "-" and operand_type not in NUMERIC_TYPES:
                self._error(f"Unary '-' requires a numeric operand, found {operand_type}", node)
                return None, None
            value = -operand_value if operand_value is not None else None
            return operand_type, value

        if isinstance(node, ast.BinaryOp):
            return self._visit_binary_op(node)

        self._error(f"Unsupported expression type in Phase 1: {type(node).__name__}", node)
        return None, None

    def _visit_binary_op(self, node: ast.BinaryOp):
        left_type, left_val = self._visit_expression(node.left)
        right_type, right_val = self._visit_expression(node.right)
        if left_type is None or right_type is None:
            return None, None

        comparison_ops = {"==", "!=", "<", ">", "<=", ">="}
        arithmetic_ops = {"+", "-", "*", "/", "%"}

        if node.operator in comparison_ops:
            if not self._types_compatible(left_type, right_type):
                self._error(
                    f"Type mismatch in comparison: {left_type} {node.operator} {right_type}",
                    node,
                )
                return None, None
            self._check(True, f"Comparison '{node.operator}' has compatible operand types")
            return "bool", None

        if node.operator in arithmetic_ops:
            if node.operator == "+" and left_type == "string" and right_type == "string":
                self._check(True, "String concatenation types valid")
                value = (left_val + right_val) if left_val is not None and right_val is not None else None
                return "string", value

            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                self._error(
                    f"Operator '{node.operator}' requires numeric operands, found {left_type} and {right_type}",
                    node,
                )
                return None, None

            result_type = "float" if "float" in (left_type, right_type) else "int"
            self._check(True, f"Arithmetic '{node.operator}' operand types valid ({result_type})")

            value = None
            if left_val is not None and right_val is not None:
                try:
                    if node.operator == "+":
                        value = left_val + right_val
                    elif node.operator == "-":
                        value = left_val - right_val
                    elif node.operator == "*":
                        value = left_val * right_val
                    elif node.operator == "/":
                        value = left_val / right_val if right_val != 0 else None
                    elif node.operator == "%":
                        value = left_val % right_val if right_val != 0 else None
                except ZeroDivisionError:
                    value = None
            return result_type, value

        self._error(f"Unknown operator '{node.operator}'", node)
        return None, None

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _types_compatible(declared_type, actual_type):
        if declared_type == actual_type:
            return True
        return declared_type in NUMERIC_TYPES and actual_type in NUMERIC_TYPES

    def _error(self, message, node):
        self.errors.append(SemanticError(message, line=getattr(node, "line", 0), column=getattr(node, "column", 0)))
        self.checks.append(f"\u2717 {message}")

    def _check(self, ok, message):
        mark = "\u2713" if ok else "\u2717"
        self.checks.append(f"{mark} {message}")


def analyze(program: ast.Program):
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
