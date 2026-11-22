from ir import IRInstruction, IRFunction, IRProgram
from ast_nodes import (
    Program, Function, Block, VariableDeclaration,
    ExpressionStatement, ReturnStatement, IfStatement,
    WhileStatement, ForStatement, BreakStatement, ContinueStatement,
    BinaryExpression, UnaryExpression, AssignmentExpression,
    VariableExpression, IntegerLiteral, BooleanLiteral, CallExpression
)


class IRGenerator:
    def __init__(self):
        self.program = IRProgram()
        self.function = None
        self.temp_count = 0
        self.label_count = 0
        self.loop_stack = []
        self.function_returns = {}

    def temp(self):
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def label(self, prefix="L"):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, op, dst=None, a=None, b=None, extra=None, line=0):
        self.function.instructions.append(
            IRInstruction(op, dst, a, b, extra, line)
        )

    def generate(self, ast):
        self.function_returns = {
            d.name: d.return_type
            for d in ast.declarations
            if isinstance(d, (Function, __import__("ast_nodes").FunctionPrototype))
        }
        for declaration in ast.declarations:
            if isinstance(declaration, Function):
                self.generate_function(declaration)
        return self.program

    def generate_function(self, node):
        self.temp_count = 0
        self.label_count = 0
        self.loop_stack = []

        params = [
            p.name if hasattr(p, "name") else str(p)
            for p in node.parameters
        ]

        self.function = IRFunction(
            node.name, node.return_type, params
        )
        self.program.functions.append(self.function)
        self.statement(node.body)

    def statement(self, node):
        if node is None:
            return

        if isinstance(node, Block):
            for item in node.statements:
                self.statement(item)

        elif isinstance(node, VariableDeclaration):
            if node.initializer is not None:
                value = self.expression(node.initializer)
                self.emit("STORE", node.name, value)

        elif isinstance(node, ExpressionStatement):
            self.expression(node.expression)

        elif isinstance(node, ReturnStatement):
            value = self.expression(node.expression) if node.expression else None
            self.emit("RET", a=value)

        elif isinstance(node, IfStatement):
            condition = self.expression(node.condition)
            else_label = self.label("else")
            end_label = self.label("endif")

            self.emit("JZ", a=condition, b=else_label)
            self.statement(node.then_branch)
            self.emit("JMP", a=end_label)
            self.emit("LABEL", a=else_label)

            if node.else_branch is not None:
                self.statement(node.else_branch)

            self.emit("LABEL", a=end_label)

        elif isinstance(node, WhileStatement):
            condition_label = self.label("while")
            end_label = self.label("endwhile")

            self.emit("LABEL", a=condition_label)
            condition = self.expression(node.condition)
            self.emit("JZ", a=condition, b=end_label)

            self.loop_stack.append((end_label, condition_label))
            try:
                self.statement(node.body)
            finally:
                self.loop_stack.pop()

            self.emit("JMP", a=condition_label)
            self.emit("LABEL", a=end_label)

        elif isinstance(node, ForStatement):
            if isinstance(node.initializer, VariableDeclaration):
                self.statement(node.initializer)
            elif node.initializer is not None:
                self.expression(node.initializer)

            condition_label = self.label("forcond")
            update_label = self.label("forupdate")
            end_label = self.label("endfor")

            self.emit("LABEL", a=condition_label)

            if node.condition is not None:
                condition = self.expression(node.condition)
                self.emit("JZ", a=condition, b=end_label)

            self.loop_stack.append((end_label, update_label))
            try:
                self.statement(node.body)
            finally:
                self.loop_stack.pop()

            self.emit("LABEL", a=update_label)

            if node.update is not None:
                self.expression(node.update)

            self.emit("JMP", a=condition_label)
            self.emit("LABEL", a=end_label)

        elif isinstance(node, BreakStatement):
            if not self.loop_stack:
                raise ValueError("'break' used outside a loop")
            self.emit("JMP", a=self.loop_stack[-1][0])

        elif isinstance(node, ContinueStatement):
            if not self.loop_stack:
                raise ValueError("'continue' used outside a loop")
            self.emit("JMP", a=self.loop_stack[-1][1])

        else:
            raise TypeError(
                f"Unsupported AST statement: {type(node).__name__}"
            )

    def expression(self, node):
        if node is None:
            return None

        if isinstance(node, IntegerLiteral):
            return str(node.value)

        if isinstance(node, BooleanLiteral):
            return "1" if node.value else "0"

        if isinstance(node, VariableExpression):
            return node.name

        if isinstance(node, AssignmentExpression):
            value = self.expression(node.value)
            if isinstance(node.target, VariableExpression):
                self.emit("STORE", node.target.name, value)
                return value
            raise TypeError("Array assignment is not supported by this backend.")

        if isinstance(node, UnaryExpression):
            operand = self.expression(node.operand)
            result = self.temp()
            operations = {"-": "NEG", "+": "MOV", "!": "NOT"}
            op = operations.get(node.operator)
            if op is None:
                raise ValueError(f"Unsupported unary operator: {node.operator}")
            self.emit(op, result, operand)
            return result

        if isinstance(node, BinaryExpression):
            result = self.temp()

            # Short-circuit AND (&&)
            if node.operator == "&&":
                false_label = self.label("and_false")
                end_label = self.label("and_end")

                left = self.expression(node.left)
                self.emit("JZ", a=left, b=false_label)

                right = self.expression(node.right)
                self.emit("JZ", a=right, b=false_label)

                self.emit("MOV", result, "1")
                self.emit("JMP", a=end_label)

                self.emit("LABEL", a=false_label)
                self.emit("MOV", result, "0")
                self.emit("LABEL", a=end_label)

                return result

            # Short-circuit OR (||)
            if node.operator == "||":
                right_label = self.label("or_right")
                true_label = self.label("or_true")
                false_label = self.label("or_false")
                end_label = self.label("or_end")

                left = self.expression(node.left)
                self.emit("JZ", a=left, b=right_label)
                self.emit("JMP", a=true_label)

                self.emit("LABEL", a=right_label)
                right = self.expression(node.right)
                self.emit("JZ", a=right, b=false_label)
                self.emit("JMP", a=true_label)

                self.emit("LABEL", a=true_label)
                self.emit("MOV", result, "1")
                self.emit("JMP", a=end_label)

                self.emit("LABEL", a=false_label)
                self.emit("MOV", result, "0")
                self.emit("LABEL", a=end_label)

                return result

            left = self.expression(node.left)
            right = self.expression(node.right)

            operations = {
                "+": "ADD", "-": "SUB", "*": "MUL",
                "/": "DIV", "%": "MOD",
                "==": "EQ", "!=": "NE",
                "<": "LT", ">": "GT",
                "<=": "LE", ">=": "GE"
            }

            op = operations.get(node.operator)
            if op is None:
                raise ValueError(f"Unsupported binary operator: {node.operator}")

            self.emit(op, result, left, right)
            return result

        if isinstance(node, CallExpression):
            arguments = [
                self.expression(argument)
                for argument in node.arguments
            ]
            returns_value = self.function_returns.get(
                node.function_name, "int"
            ) != "void"
            result = self.temp() if returns_value else None
            self.emit(
                "CALL", result, node.function_name,
                extra=",".join(arguments)
            )
            return result

        raise TypeError(
            f"Unsupported AST expression: {type(node).__name__}"
        )


def generate_ir(program_ast, semantic_result=None):
    if semantic_result is not None and not semantic_result.ok:
        raise ValueError("Cannot generate IR when semantic errors exist.")

    return IRGenerator().generate(program_ast)
