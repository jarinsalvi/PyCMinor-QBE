from dataclasses import dataclass
from typing import List

from symbol_table import SymbolTable
from ast_nodes import (
    Function, FunctionPrototype, VariableDeclaration, ArrayDeclaration, Block,
    ExpressionStatement, ReturnStatement, IfStatement,
    WhileStatement, ForStatement, BreakStatement, ContinueStatement,
    BinaryExpression, UnaryExpression,
    AssignmentExpression, VariableExpression, ArrayAccess,
    CallExpression, IntegerLiteral, BooleanLiteral
)


@dataclass
class Diagnostic:
    code: str
    severity: str
    file: str
    line: int
    column: int
    message: str


@dataclass
class SemanticResult:
    ok: bool
    symbol_table: SymbolTable
    diagnostics: List[Diagnostic]


class SemanticAnalyzer:
    def __init__(self, file_path="main.cm"):
        self.file_path = file_path
        self.symbol_table = SymbolTable()
        self.diagnostics = []
        self.loop_depth = 0

    def add_error(self, code, line, col, msg):
        self.diagnostics.append(Diagnostic(
            code=code,
            severity="error",
            file=self.file_path,
            line=line,
            column=col,
            message=msg
        ))

    def position(self, node):
        return (
            getattr(node, "line", 1),
            getattr(node, "column", 1)
        )

    def analyze(self, program_ast):
        # Register prototypes and definitions before checking function bodies.
        for decl in program_ast.declarations:
            if isinstance(decl, (Function, FunctionPrototype)):
                line, col = self.position(decl)
                param_types = [p.param_type for p in decl.parameters]
                is_definition = isinstance(decl, Function)

                _, error = self.symbol_table.declare_function(
                    decl.name,
                    decl.return_type,
                    param_types,
                    line,
                    col,
                    is_definition
                )

                if error:
                    self.add_error("E004", line, col, error)

        # Every declared function must have exactly one definition.
        for name, sym in self.symbol_table.global_functions.items():
            if not sym.is_defined:
                self.add_error(
                    "E012", sym.line, sym.column,
                    f"Function '{name}' is declared but not defined"
                )

        main_sym = self.symbol_table.global_functions.get("main")

        if not main_sym or not main_sym.is_defined:
            self.add_error(
                "E001", 1, 1,
                "Missing main function definition"
            )
        elif main_sym.return_type != "int" or main_sym.param_types:
            self.add_error(
                "E002", main_sym.line, main_sym.column,
                "main must be defined as 'int main(void)'"
            )

        # Analyze definitions only; prototypes have no body.
        for decl in program_ast.declarations:
            if isinstance(decl, Function):
                self._visit_decl(decl)

        ok = not any(d.severity == "error" for d in self.diagnostics)

        return SemanticResult(
            ok=ok,
            symbol_table=self.symbol_table,
            diagnostics=self.diagnostics
        )

    def _visit_decl(self, decl):
        if not isinstance(decl, Function):
            return

        self.symbol_table.enter_scope()

        for param in decl.parameters:
            line, col = self.position(param)
            sym = self.symbol_table.declare_variable(
                param.name,
                param.param_type,
                "parameter",
                line,
                col
            )

            if sym is None:
                self.add_error(
                    "E005", line, col,
                    f"Duplicate parameter '{param.name}'"
                )

        self._visit_statement(decl.body)
        self.symbol_table.exit_scope()

    def _visit_statement(self, node):
        if node is None:
            return

        if isinstance(node, Block):
            self.symbol_table.enter_scope()

            for statement in node.statements:
                self._visit_statement(statement)

            self.symbol_table.exit_scope()

        elif isinstance(node, VariableDeclaration):
            line, col = self.position(node)

            sym = self.symbol_table.declare_variable(
                node.name,
                node.var_type,
                "local",
                line,
                col
            )

            if sym is None:
                self.add_error(
                    "E006", line, col,
                    f"Duplicate variable '{node.name}'"
                )

            if node.initializer is not None:
                self._visit_expression(node.initializer)

        elif isinstance(node, ArrayDeclaration):
            line, col = self.position(node)

            sym = self.symbol_table.declare_variable(
                node.name,
                node.element_type,
                "local",
                line,
                col
            )

            if sym is None:
                self.add_error(
                    "E006", line, col,
                    f"Duplicate variable '{node.name}'"
                )

        elif isinstance(node, ExpressionStatement):
            self._visit_expression(node.expression)

        elif isinstance(node, ReturnStatement):
            self._visit_expression(node.expression)

        elif isinstance(node, IfStatement):
            self._visit_expression(node.condition)
            self._visit_statement(node.then_branch)
            self._visit_statement(node.else_branch)

        elif isinstance(node, WhileStatement):
            self._visit_expression(node.condition)

            self.loop_depth += 1
            try:
                self._visit_statement(node.body)
            finally:
                self.loop_depth -= 1

        elif isinstance(node, ForStatement):
            # The initializer variable belongs to the for-loop scope.
            self.symbol_table.enter_scope()
            try:
                if isinstance(node.initializer, VariableDeclaration):
                    self._visit_statement(node.initializer)
                else:
                    self._visit_expression(node.initializer)

                self._visit_expression(node.condition)
                self._visit_expression(node.update)

                self.loop_depth += 1
                try:
                    self._visit_statement(node.body)
                finally:
                    self.loop_depth -= 1
            finally:
                self.symbol_table.exit_scope()

        elif isinstance(node, BreakStatement):
            if self.loop_depth == 0:
                line, col = self.position(node)
                self.add_error(
                    "E010", line, col,
                    "'break' statement is only valid inside a loop"
                )

        elif isinstance(node, ContinueStatement):
            if self.loop_depth == 0:
                line, col = self.position(node)
                self.add_error(
                    "E011", line, col,
                    "'continue' statement is only valid inside a loop"
                )

    def _infer_expression_type(self, node):
        """Infer the basic type of an expression."""

        if node is None:
            return None

        if isinstance(node, IntegerLiteral):
            return "int"

        if isinstance(node, BooleanLiteral):
            return "bool"

        if isinstance(node, VariableExpression):
            sym = self.symbol_table.lookup_variable(node.name)
            return sym.type_name if sym else None

        if isinstance(node, ArrayAccess):
            sym = self.symbol_table.lookup_variable(node.array_name)
            return sym.type_name if sym else None

        if isinstance(node, CallExpression):
            sym = self.symbol_table.global_functions.get(node.function_name)
            return sym.return_type if sym else None

        if isinstance(node, AssignmentExpression):
            return self._infer_expression_type(node.target)

        if isinstance(node, UnaryExpression):
            if node.operator == "!":
                return "bool"
            return self._infer_expression_type(node.operand)

        if isinstance(node, BinaryExpression):
            if node.operator in {
                "==", "!=", "<", "<=", ">", ">=", "&&", "||"
            }:
                return "bool"
            return self._infer_expression_type(node.left)

        return None

    def _visit_expression(self, node):
        if node is None:
            return

        if isinstance(node, VariableExpression):
            if self.symbol_table.lookup_variable(node.name) is None:
                line, col = self.position(node)
                self.add_error(
                    "E007", line, col,
                    f"Undeclared variable '{node.name}'"
                )

        elif isinstance(node, ArrayAccess):
            if self.symbol_table.lookup_variable(node.array_name) is None:
                line, col = self.position(node)
                self.add_error(
                    "E007", line, col,
                    f"Undeclared array '{node.array_name}'"
                )
            self._visit_expression(node.index)

        elif isinstance(node, BinaryExpression):
            self._visit_expression(node.left)
            self._visit_expression(node.right)

            left_type = self._infer_expression_type(node.left)
            right_type = self._infer_expression_type(node.right)

            arithmetic_ops = {"+", "-", "*", "/", "%"}
            comparison_ops = {"<", "<=", ">", ">="}
            equality_ops = {"==", "!="}
            logical_ops = {"&&", "||"}

            if node.operator in arithmetic_ops | comparison_ops:
                if left_type and left_type != "int":
                    line, col = self.position(node)
                    self.add_error(
                        "E014", line, col,
                        f"Operator '{node.operator}' requires int operands"
                    )
                if right_type and right_type != "int":
                    line, col = self.position(node)
                    self.add_error(
                        "E014", line, col,
                        f"Operator '{node.operator}' requires int operands"
                    )

            elif node.operator in equality_ops | logical_ops:
                if left_type and right_type and left_type != right_type:
                    line, col = self.position(node)
                    self.add_error(
                        "E014", line, col,
                        f"Operator '{node.operator}' has incompatible operand types"
                    )

        elif isinstance(node, UnaryExpression):
            self._visit_expression(node.operand)

            operand_type = self._infer_expression_type(node.operand)

            if node.operator == "!" and operand_type and operand_type != "bool":
                line, col = self.position(node)
                self.add_error(
                    "E015", line, col,
                    "Logical NOT operator '!' requires a bool operand"
                )

            elif node.operator == "-" and operand_type and operand_type != "int":
                line, col = self.position(node)
                self.add_error(
                    "E015", line, col,
                    "Unary minus operator '-' requires an int operand"
                )

        elif isinstance(node, AssignmentExpression):
            self._visit_expression(node.target)
            self._visit_expression(node.value)

        elif isinstance(node, CallExpression):
            line, col = self.position(node)
            function = self.symbol_table.global_functions.get(
                node.function_name
            )

            if function is None:
                self.add_error(
                    "E008", line, col,
                    f"Undeclared function '{node.function_name}'"
                )
            elif len(node.arguments) != len(function.param_types):
                self.add_error(
                    "E009", line, col,
                    f"Function '{node.function_name}' expects "
                    f"{len(function.param_types)} arguments, "
                    f"but got {len(node.arguments)}"
                )

            for argument in node.arguments:
                self._visit_expression(argument)

            if function is not None:
                for index, (argument, expected_type) in enumerate(
                    zip(node.arguments, function.param_types), start=1
                ):
                    actual_type = self._infer_expression_type(argument)

                    if actual_type is not None and actual_type != expected_type:
                        line, col = self.position(argument)
                        self.add_error(
                            "E013", line, col,
                            f"Argument {index} of function "
                            f"'{node.function_name}' expects "
                            f"'{expected_type}', but got '{actual_type}'"
                        )


def analyze(program_ast, file_path="main.cm"):
    analyzer = SemanticAnalyzer(file_path)
    return analyzer.analyze(program_ast)


def dump_symbols(semantic_result):
    print("--- Symbol Table Dump ---")

    for name, sym in semantic_result.symbol_table.global_functions.items():
        print(
            f"Function: {name} | Return: {sym.return_type} | "
            f"Params: {sym.param_types} | Defined: {sym.is_defined}"
        )
