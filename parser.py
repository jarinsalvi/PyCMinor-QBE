
from typing import List, Optional

from lexer import Lexer, LexerError, Token, tokenize
from ast_nodes import (
    ASTNode,
    Program,
    Function,
    FunctionPrototype,
    Parameter,
    VariableDeclaration,
    ArrayDeclaration,
    Block,
    ExpressionStatement,
    ReturnStatement,
    IfStatement,
    WhileStatement,
    ForStatement,
    BreakStatement,
    ContinueStatement,
    BinaryExpression,
    UnaryExpression,
    AssignmentExpression,
    VariableExpression,
    IntegerLiteral,
    BooleanLiteral,
    CallExpression,
    ArrayAccess,
)


# ==========================================
# 1. PARSER ERROR
# ==========================================

class ParserError(Exception):
    """Raised when invalid syntax is found."""
    pass


# ==========================================
# 2. PARSER CLASS
# ==========================================

class Parser:
    """Handwritten Recursive Descent Parser for CMinor."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0

    # --------------------------------------
    # Current token
    # --------------------------------------

    def current_token(self) -> Token:
        return self.tokens[self.position]

    # --------------------------------------
    # Check current token type
    # --------------------------------------

    def check(self, token_type: str) -> bool:
        return self.current_token().type == token_type

    # --------------------------------------
    # Move to next token
    # --------------------------------------

    def advance(self) -> Token:
        token = self.current_token()

        if token.type != "EOF":
            self.position += 1

        return token

    # --------------------------------------
    # Match and consume expected token
    # --------------------------------------

    def expect(self, token_type: str) -> Token:

        token = self.current_token()

        if token.type != token_type:
            raise ParserError(
                f"Expected {token_type}, "
                f"but found {token.type} "
                f"({token.value!r}) at "
                f"line {token.line}, "
                f"column {token.column}"
            )

        return self.advance()

    # --------------------------------------
    # Check whether token is a data type
    # --------------------------------------

    def is_type(self) -> bool:
        return self.check("INT") or self.check("VOID") or self.check("BOOL")

    # --------------------------------------
    # Read a data type
    # --------------------------------------

    def parse_type(self) -> str:

        if not self.is_type():
            token = self.current_token()

            raise ParserError(
                f"Expected a data type at "
                f"line {token.line}, "
                f"column {token.column}"
            )

        return self.advance().value

    # ======================================
    # 3. PROGRAM
    # ======================================

    def parse(self) -> Program:
        """Parse the complete program."""

        declarations = []

        while not self.check("EOF"):

            if not self.is_type():
                token = self.current_token()

                raise ParserError(
                    f"Unexpected token {token.value!r} "
                    f"at line {token.line}, "
                    f"column {token.column}"
                )

            declarations.append(self.parse_declaration())

        self.expect("EOF")

        return Program(declarations=declarations)

    # ======================================
    # 4. FUNCTION / VARIABLE DECLARATION
    # ======================================

    def parse_declaration(self) -> ASTNode:

        data_type = self.parse_type()

        name = self.expect("IDENTIFIER").value

        # Function declaration
        if self.check("LPAREN"):

            return self.parse_function(data_type, name)

        # Global variable or array declaration
        return self.parse_variable_declaration(
            data_type,
            name
        )

    # --------------------------------------
    # Function declaration
    # --------------------------------------

    def parse_function(self, return_type: str, name: str) -> ASTNode:
        self.expect("LPAREN")
        parameters = []

        if self.check("RPAREN"):
            self.advance()
        elif self.check("VOID"):
            self.advance()
            self.expect("RPAREN")
        else:
            parameters = self.parse_parameters(allow_unnamed=True)
            self.expect("RPAREN")

        # Prototype: int sum(int);
        if self.check("SEMICOLON"):
            self.advance()
            return FunctionPrototype(
                return_type=return_type,
                name=name,
                parameters=parameters
            )

        # Definitions require parameter names.
        for param in parameters:
            if not param.name:
                token = self.current_token()
                raise ParserError(
                    f"Function definition parameters need names "
                    f"at line {token.line}"
                )

        body = self.parse_block()
        return Function(
            return_type=return_type,
            name=name,
            parameters=parameters,
            body=body
        )

    def parse_parameters(self, allow_unnamed=False) -> List[Parameter]:
        parameters = []

        while True:
            param_type = self.parse_type()

            if param_type == "void":
                token = self.current_token()
                raise ParserError(
                    f"void parameter must be the only "
                    f"parameter at line {token.line}"
                )

            param_name = ""
            if self.check("IDENTIFIER"):
                param_name = self.advance().value
            elif not allow_unnamed:
                self.expect("IDENTIFIER")

            parameters.append(Parameter(
                param_type=param_type,
                name=param_name
            ))

            if not self.check("COMMA"):
                break
            self.advance()

        return parameters

    # ======================================
    # 5. VARIABLE DECLARATION
    # ======================================

    def parse_variable_declaration(
        self,
        var_type: str,
        name: str,
        consume_semicolon: bool = True
    ) -> ASTNode:

        # Array declaration
        if self.check("LBRACKET"):

            self.advance()

            size = None

            if not self.check("RBRACKET"):

                size_token = self.expect("INTEGER")
                size = int(size_token.value)

            self.expect("RBRACKET")
            if consume_semicolon:
                self.expect("SEMICOLON")

            return ArrayDeclaration(
                element_type=var_type,
                name=name,
                size=size
            )

        # Normal variable declaration
        initializer = None

        if self.check("ASSIGN"):

            self.advance()

            initializer = self.parse_expression()

        if consume_semicolon:
            self.expect("SEMICOLON")

        return VariableDeclaration(
            var_type=var_type,
            name=name,
            initializer=initializer
        )

    # ======================================
    # 6. BLOCK
    # ======================================

    def parse_block(self) -> Block:

        self.expect("LBRACE")

        statements = []

        while not self.check("RBRACE"):

            if self.check("EOF"):
                token = self.current_token()

                raise ParserError(
                    f"Unterminated block at "
                    f"line {token.line}"
                )

            statements.append(self.parse_statement())

        self.expect("RBRACE")

        return Block(statements=statements)

    # ======================================
    # 7. STATEMENTS
    # ======================================

    def parse_statement(self) -> ASTNode:

        # Block statement
        if self.check("LBRACE"):
            return self.parse_block()

        # Variable declaration
        if self.is_type():

            var_type = self.parse_type()

            name = self.expect("IDENTIFIER").value

            return self.parse_variable_declaration(
                var_type,
                name
            )

        # Return statement
        if self.check("RETURN"):
            return self.parse_return_statement()

        # If statement
        if self.check("IF"):
            return self.parse_if_statement()

        # While statement
        if self.check("WHILE"):
            return self.parse_while_statement()

        # For statement
        if self.check("FOR"):
            return self.parse_for_statement()

        # Break statement
        if self.check("BREAK"):
            self.advance()
            self.expect("SEMICOLON")
            return BreakStatement()

        # Continue statement
        if self.check("CONTINUE"):
            self.advance()
            self.expect("SEMICOLON")
            return ContinueStatement()

        # Empty statement
        if self.check("SEMICOLON"):
            self.advance()
            return ExpressionStatement()

        # Expression statement
        expression = self.parse_expression()

        self.expect("SEMICOLON")

        return ExpressionStatement(
            expression=expression
        )

    # --------------------------------------
    # Return statement
    # --------------------------------------

    def parse_return_statement(self) -> ReturnStatement:

        self.expect("RETURN")

        expression = None

        if not self.check("SEMICOLON"):
            expression = self.parse_expression()

        self.expect("SEMICOLON")

        return ReturnStatement(
            expression=expression
        )

    # --------------------------------------
    # If / Else statement
    # --------------------------------------

    def parse_if_statement(self) -> IfStatement:

        self.expect("IF")
        self.expect("LPAREN")

        condition = self.parse_expression()

        self.expect("RPAREN")

        then_branch = self.parse_statement()

        else_branch = None

        if self.check("ELSE"):

            self.advance()

            else_branch = self.parse_statement()

        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch
        )

    # --------------------------------------
    # While statement
    # --------------------------------------

    def parse_while_statement(self) -> WhileStatement:

        self.expect("WHILE")
        self.expect("LPAREN")

        condition = self.parse_expression()

        self.expect("RPAREN")

        body = self.parse_statement()

        return WhileStatement(
            condition=condition,
            body=body
        )

    # --------------------------------------
    # For statement
    # --------------------------------------

    def parse_for_statement(self) -> ForStatement:

        self.expect("FOR")
        self.expect("LPAREN")

        initializer = None

        if not self.check("SEMICOLON"):

            if self.is_type():
                var_type = self.parse_type()
                name = self.expect("IDENTIFIER").value

                initializer = self.parse_variable_declaration(
                    var_type,
                    name,
                    consume_semicolon=False
                )
            else:
                initializer = self.parse_expression()

        self.expect("SEMICOLON")

        condition = None

        if not self.check("SEMICOLON"):
            condition = self.parse_expression()

        self.expect("SEMICOLON")

        update = None

        if not self.check("RPAREN"):
            update = self.parse_expression()

        self.expect("RPAREN")

        body = self.parse_statement()

        return ForStatement(
            initializer=initializer,
            condition=condition,
            update=update,
            body=body
        )

    # ======================================
    # 8. EXPRESSIONS
    # ======================================

    def parse_expression(self) -> ASTNode:
        return self.parse_assignment()

    # --------------------------------------
    # Assignment
    # --------------------------------------

    def parse_assignment(self) -> ASTNode:

        left = self.parse_logical_or()

        if self.check("ASSIGN"):

            self.advance()

            value = self.parse_assignment()

            if not isinstance(
                left,
                (VariableExpression, ArrayAccess)
            ):
                token = self.current_token()

                raise ParserError(
                    f"Invalid assignment target "
                    f"at line {token.line}"
                )

            return AssignmentExpression(
                target=left,
                value=value
            )

        return left

    # --------------------------------------
    # Logical OR
    # --------------------------------------

    def parse_logical_or(self) -> ASTNode:

        expression = self.parse_logical_and()

        while self.check("LOGICAL_OR"):

            operator = self.advance().value

            right = self.parse_logical_and()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Logical AND
    # --------------------------------------

    def parse_logical_and(self) -> ASTNode:

        expression = self.parse_equality()

        while self.check("LOGICAL_AND"):

            operator = self.advance().value

            right = self.parse_equality()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Equality
    # --------------------------------------

    def parse_equality(self) -> ASTNode:

        expression = self.parse_comparison()

        while self.check("EQUAL") or self.check("NOT_EQUAL"):

            operator = self.advance().value

            right = self.parse_comparison()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Comparison
    # --------------------------------------

    def parse_comparison(self) -> ASTNode:

        expression = self.parse_additive()

        while (
            self.check("LESS_THAN")
            or self.check("GREATER_THAN")
            or self.check("LESS_EQUAL")
            or self.check("GREATER_EQUAL")
        ):

            operator = self.advance().value

            right = self.parse_additive()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Addition and subtraction
    # --------------------------------------

    def parse_additive(self) -> ASTNode:

        expression = self.parse_multiplicative()

        while self.check("PLUS") or self.check("MINUS"):

            operator = self.advance().value

            right = self.parse_multiplicative()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Multiplication, division, modulo
    # --------------------------------------

    def parse_multiplicative(self) -> ASTNode:

        expression = self.parse_unary()

        while (
            self.check("MULTIPLY")
            or self.check("DIVIDE")
            or self.check("MODULO")
        ):

            operator = self.advance().value

            right = self.parse_unary()

            expression = BinaryExpression(
                left=expression,
                operator=operator,
                right=right
            )

        return expression

    # --------------------------------------
    # Unary expressions
    # --------------------------------------

    def parse_unary(self) -> ASTNode:

        if (
            self.check("MINUS")
            or self.check("PLUS")
            or self.check("LOGICAL_NOT")
        ):

            operator = self.advance().value

            operand = self.parse_unary()

            return UnaryExpression(
                operator=operator,
                operand=operand
            )

        return self.parse_postfix()

    # ======================================
    # 9. POSTFIX EXPRESSIONS
    # ======================================

    def parse_postfix(self) -> ASTNode:

        expression = self.parse_primary()

        while True:

            # Array access
            if self.check("LBRACKET"):

                self.advance()

                index = self.parse_expression()

                self.expect("RBRACKET")

                if not isinstance(expression, VariableExpression):
                    token = self.current_token()
                    raise ParserError(
                        f"Invalid array access at line {token.line}"
                    )

                expression = ArrayAccess(
                    array_name=expression.name,
                    index=index
                )

            # Function call
            elif self.check("LPAREN"):

                self.advance()

                arguments = []

                if not self.check("RPAREN"):

                    arguments = self.parse_arguments()

                self.expect("RPAREN")

                if not isinstance(expression, VariableExpression):
                    token = self.current_token()
                    raise ParserError(
                        f"Invalid function call at line {token.line}"
                    )

                expression = CallExpression(
                    function_name=expression.name,
                    arguments=arguments
                )

            else:
                break

        return expression

    # --------------------------------------
    # Function call arguments
    # --------------------------------------

    def parse_arguments(self) -> List[ASTNode]:

        arguments = []

        while True:

            arguments.append(self.parse_expression())

            if not self.check("COMMA"):
                break

            self.advance()

        return arguments

    # ======================================
    # 10. PRIMARY EXPRESSIONS
    # ======================================

    def parse_primary(self) -> ASTNode:

        # Integer literal
        if self.check("INTEGER"):

            value = int(self.advance().value)

            return IntegerLiteral(value=value)

        # Boolean true
        if self.check("TRUE"):

            self.advance()

            return BooleanLiteral(value=True)

        # Boolean false
        if self.check("FALSE"):

            self.advance()

            return BooleanLiteral(value=False)

        # Identifier
        if self.check("IDENTIFIER"):

            name = self.advance().value

            return VariableExpression(name=name)

        # Parenthesized expression
        if self.check("LPAREN"):

            self.advance()

            expression = self.parse_expression()

            self.expect("RPAREN")

            return expression

        token = self.current_token()

        raise ParserError(
            f"Unexpected token {token.value!r} "
            f"at line {token.line}, "
            f"column {token.column}"
        )


# ==========================================
# 11. CONVENIENCE FUNCTION
# ==========================================

def parse_tokens(tokens: List[Token]) -> Program:
    """Parses a token list and returns an AST."""

    parser = Parser(tokens)

    return parser.parse()


def parse(source_code: str) -> Program:
    """Tokenizes and parses source code."""

    tokens = tokenize(source_code)

    return parse_tokens(tokens)


# ==========================================
# 12. MANUAL TESTING
# ==========================================

if __name__ == "__main__":

    source_code = """
    int add(int a, int b) {
        return a + b;
    }

    int main(void) {

        int x = 10;
        int y = 20;

        int result = add(x, y);

        if (result >= 30) {
            return result;
        } else {
            return 0;
        }
    }
    """

    try:

        ast = parse(source_code)

        print("\n========== PARSER SUCCESS ==========\n")

        from ast_nodes import print_ast

        print_ast(ast)

    except (LexerError, ParserError) as error:

        print("\nCOMPILATION ERROR:")
        print(error)
