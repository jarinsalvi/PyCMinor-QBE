
from dataclasses import dataclass, field
from typing import List, Optional


# Base class for all AST nodes
@dataclass
class ASTNode:
    pass


# Function parameter
@dataclass
class Parameter(ASTNode):
    param_type: str
    name: str


# Complete program
@dataclass
class Program(ASTNode):
    declarations: List[ASTNode] = field(default_factory=list)


# Function declaration
@dataclass
class Function(ASTNode):
    return_type: str
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    body: Optional[ASTNode] = None


# Variable declaration
@dataclass
class VariableDeclaration(ASTNode):
    var_type: str
    name: str
    initializer: Optional[ASTNode] = None


# Array declaration
@dataclass
class ArrayDeclaration(ASTNode):
    element_type: str
    name: str
    size: Optional[int] = None


# Array access
@dataclass
class ArrayAccess(ASTNode):
    array_name: str
    index: ASTNode


# Block of statements
@dataclass
class Block(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


# Expression statement
@dataclass
class ExpressionStatement(ASTNode):
    expression: Optional[ASTNode] = None


# Return statement
@dataclass
class ReturnStatement(ASTNode):
    expression: Optional[ASTNode] = None


# If-else statement
@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None


# While loop
@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: ASTNode


# Binary expression: a + b, a > b, etc.
@dataclass
class BinaryExpression(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode


# Unary expression: -a, !a, etc.
@dataclass
class UnaryExpression(ASTNode):
    operator: str
    operand: ASTNode


# Assignment expression: a = 10
@dataclass
class AssignmentExpression(ASTNode):
    target: ASTNode
    value: ASTNode


# Variable reference
@dataclass
class VariableExpression(ASTNode):
    name: str


# Integer literal
@dataclass
class IntegerLiteral(ASTNode):
    value: int


# Boolean literal
@dataclass
class BooleanLiteral(ASTNode):
    value: bool


# Function call
@dataclass
class CallExpression(ASTNode):
    function_name: str
    arguments: List[ASTNode] = field(default_factory=list)


# Print AST in a readable tree format
def print_ast(node: Optional[ASTNode], indent: int = 0) -> None:

    if node is None:
        print(" " * indent + "None")
        return

    prefix = " " * indent

    if isinstance(node, Program):
        print(prefix + "Program")
        for declaration in node.declarations:
            print_ast(declaration, indent + 2)

    elif isinstance(node, Function):
        print(prefix + f"Function: {node.return_type} {node.name}")
        print(prefix + "  Parameters:")
        for parameter in node.parameters:
            print_ast(parameter, indent + 4)
        print(prefix + "  Body:")
        print_ast(node.body, indent + 4)

    elif isinstance(node, Parameter):
        print(prefix + f"Parameter: {node.param_type} {node.name}")

    elif isinstance(node, VariableDeclaration):
        print(prefix + f"VariableDeclaration: {node.var_type} {node.name}")
        if node.initializer is not None:
            print(prefix + "  Initializer:")
            print_ast(node.initializer, indent + 4)

    elif isinstance(node, ArrayDeclaration):
        print(prefix + f"ArrayDeclaration: {node.element_type} {node.name}[{node.size}]")

    elif isinstance(node, ArrayAccess):
        print(prefix + f"ArrayAccess: {node.array_name}")
        print(prefix + "  Index:")
        print_ast(node.index, indent + 4)

    elif isinstance(node, Block):
        print(prefix + "Block")
        for statement in node.statements:
            print_ast(statement, indent + 2)

    elif isinstance(node, ExpressionStatement):
        print(prefix + "ExpressionStatement")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, ReturnStatement):
        print(prefix + "ReturnStatement")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, IfStatement):
        print(prefix + "IfStatement")
        print(prefix + "  Condition:")
        print_ast(node.condition, indent + 4)
        print(prefix + "  Then:")
        print_ast(node.then_branch, indent + 4)

        if node.else_branch is not None:
            print(prefix + "  Else:")
            print_ast(node.else_branch, indent + 4)

    elif isinstance(node, WhileStatement):
        print(prefix + "WhileStatement")
        print(prefix + "  Condition:")
        print_ast(node.condition, indent + 4)
        print(prefix + "  Body:")
        print_ast(node.body, indent + 4)

    elif isinstance(node, BinaryExpression):
        print(prefix + f"BinaryExpression: {node.operator}")
        print_ast(node.left, indent + 2)
        print_ast(node.right, indent + 2)

    elif isinstance(node, UnaryExpression):
        print(prefix + f"UnaryExpression: {node.operator}")
        print_ast(node.operand, indent + 2)

    elif isinstance(node, AssignmentExpression):
        print(prefix + "AssignmentExpression")
        print(prefix + "  Target:")
        print_ast(node.target, indent + 4)
        print(prefix + "  Value:")
        print_ast(node.value, indent + 4)

    elif isinstance(node, VariableExpression):
        print(prefix + f"VariableExpression: {node.name}")

    elif isinstance(node, IntegerLiteral):
        print(prefix + f"IntegerLiteral: {node.value}")

    elif isinstance(node, BooleanLiteral):
        print(prefix + f"BooleanLiteral: {node.value}")

    elif isinstance(node, CallExpression):
        print(prefix + f"CallExpression: {node.function_name}")
        for argument in node.arguments:
            print_ast(argument, indent + 2)

    else:
        print(prefix + f"Unknown AST Node: {node}")


# Simple manual test
if __name__ == "__main__":

    program = Program(
        declarations=[
            Function(
                return_type="int",
                name="main",
                parameters=[],
                body=Block(
                    statements=[
                        VariableDeclaration(
                            var_type="int",
                            name="x",
                            initializer=IntegerLiteral(10)
                        ),
                        ReturnStatement(
                            expression=VariableExpression("x")
                        )
                    ]
                )
            )
        ]
    )

    print_ast(program)


# Function prototype (declaration without a body)
@dataclass
class FunctionPrototype(ASTNode):
    return_type: str
    name: str
    parameters: List[Parameter] = field(default_factory=list)


# For loop
@dataclass
class ForStatement(ASTNode):
    initializer: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: ASTNode


# Break statement
@dataclass
class BreakStatement(ASTNode):
    pass


# Continue statement
@dataclass
class ContinueStatement(ASTNode):
    pass
