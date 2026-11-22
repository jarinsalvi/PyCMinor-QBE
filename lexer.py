
from dataclasses import dataclass
from typing import List


# ==========================================
# 1. TOKEN STRUCTURE
# ==========================================

@dataclass
class Token:
    """Represents a single token."""
    type: str
    value: str
    line: int
    column: int

    def __repr__(self):
        return (
            f"Token({self.type}, {self.value!r}, "
            f"line={self.line}, column={self.column})"
        )


# ==========================================
# 2. LEXER ERROR
# ==========================================

class LexerError(Exception):
    """Raised when an invalid character or comment is found."""
    pass


# ==========================================
# 3. KEYWORDS
# ==========================================

KEYWORDS = {
    "int": "INT",
    "void": "VOID",
    "bool": "BOOL",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "break": "BREAK",
    "continue": "CONTINUE",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
}


# ==========================================
# 4. OPERATORS
# ==========================================

OPERATORS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "%": "MODULO",

    "=": "ASSIGN",
    "==": "EQUAL",
    "!=": "NOT_EQUAL",

    "<": "LESS_THAN",
    ">": "GREATER_THAN",
    "<=": "LESS_EQUAL",
    ">=": "GREATER_EQUAL",

    "&&": "LOGICAL_AND",
    "||": "LOGICAL_OR",
    "!": "LOGICAL_NOT",
}


# ==========================================
# 5. SEPARATORS
# ==========================================

SEPARATORS = {
    ";": "SEMICOLON",
    ",": "COMMA",

    "(": "LPAREN",
    ")": "RPAREN",

    "{": "LBRACE",
    "}": "RBRACE",

    "[": "LBRACKET",
    "]": "RBRACKET",
}


# ==========================================
# 6. LEXER CLASS
# ==========================================

class Lexer:
    """Handwritten lexer for the CMinor language."""

    def __init__(self, source_code: str):
        self.source = source_code

        self.position = 0
        self.line = 1
        self.column = 1

        self.tokens: List[Token] = []

    # --------------------------------------
    # Check whether input is finished
    # --------------------------------------

    def is_at_end(self):
        return self.position >= len(self.source)

    # --------------------------------------
    # Read current character
    # --------------------------------------

    def current_char(self):
        if self.is_at_end():
            return "\0"

        return self.source[self.position]

    # --------------------------------------
    # Read next character
    # --------------------------------------

    def peek(self, offset=1):
        index = self.position + offset

        if index >= len(self.source):
            return "\0"

        return self.source[index]

    # --------------------------------------
    # Move to next character
    # --------------------------------------

    def advance(self):
        if self.is_at_end():
            return "\0"

        char = self.source[self.position]
        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    # --------------------------------------
    # Add token to token list
    # --------------------------------------

    def add_token(self, token_type, value, line, column):
        token = Token(
            type=token_type,
            value=value,
            line=line,
            column=column
        )

        self.tokens.append(token)

    # ======================================
    # 7. SKIP WHITESPACE
    # ======================================

    def skip_whitespace(self):
        while not self.is_at_end():

            if self.current_char() in " \t\r\n":
                self.advance()

            else:
                break

    # ======================================
    # 8. IDENTIFIER AND KEYWORD
    # ======================================

    def read_identifier(self):

        start_line = self.line
        start_column = self.column

        identifier = ""

        while (
            self.current_char().isalnum()
            or self.current_char() == "_"
        ):
            identifier += self.advance()

        # Check whether identifier is a keyword
        token_type = KEYWORDS.get(identifier, "IDENTIFIER")

        self.add_token(
            token_type,
            identifier,
            start_line,
            start_column
        )

    # ======================================
    # 9. INTEGER LITERAL
    # ======================================

    def read_number(self):

        start_line = self.line
        start_column = self.column

        number = ""

        while self.current_char().isdigit():
            number += self.advance()

        self.add_token(
            "INTEGER",
            number,
            start_line,
            start_column
        )

    # ======================================
    # 10. READ OPERATORS
    # ======================================

    def read_operator(self):

        start_line = self.line
        start_column = self.column

        char = self.current_char()

        # Check two-character operators first
        two_char = char + self.peek()

        if two_char in OPERATORS:

            self.advance()
            self.advance()

            self.add_token(
                OPERATORS[two_char],
                two_char,
                start_line,
                start_column
            )

            return

        # Check single-character operators
        if char in OPERATORS:

            self.advance()

            self.add_token(
                OPERATORS[char],
                char,
                start_line,
                start_column
            )

            return

        raise LexerError(
            f"Unknown operator '{char}' "
            f"at line {start_line}, column {start_column}"
        )

    # ======================================
    # 11. READ SEPARATORS
    # ======================================

    def read_separator(self):

        start_line = self.line
        start_column = self.column

        char = self.advance()

        self.add_token(
            SEPARATORS[char],
            char,
            start_line,
            start_column
        )

    # ======================================
    # 12. SINGLE-LINE COMMENTS
    # ======================================

    def skip_single_line_comment(self):

        while not self.is_at_end():

            if self.current_char() == "\n":
                break

            self.advance()

    # ======================================
    # 13. MULTI-LINE COMMENTS
    # ======================================

    def skip_multi_line_comment(self):

        start_line = self.line
        start_column = self.column

        # Skip /*
        self.advance()
        self.advance()

        while not self.is_at_end():

            if (
                self.current_char() == "*"
                and self.peek() == "/"
            ):
                # Skip */
                self.advance()
                self.advance()
                return

            self.advance()

        raise LexerError(
            f"Unterminated comment starting at "
            f"line {start_line}, column {start_column}"
        )

    # ======================================
    # 14. MAIN TOKENIZATION FUNCTION
    # ======================================

    def tokenize(self):

        while not self.is_at_end():

            self.skip_whitespace()

            if self.is_at_end():
                break

            char = self.current_char()

            # Save starting position
            start_line = self.line
            start_column = self.column

            # --------------------------------
            # Comments
            # --------------------------------

            if char == "/" and self.peek() == "/":

                self.advance()
                self.advance()

                self.skip_single_line_comment()

            elif char == "/" and self.peek() == "*":

                self.skip_multi_line_comment()

            # --------------------------------
            # Identifiers and Keywords
            # --------------------------------

            elif char.isalpha() or char == "_":

                self.read_identifier()

            # --------------------------------
            # Integer Literals
            # --------------------------------

            elif char.isdigit():

                self.read_number()

            # --------------------------------
            # Operators
            # --------------------------------

            elif char in OPERATORS:

                self.read_operator()

            # --------------------------------
            # Separators
            # --------------------------------

            elif char in SEPARATORS:

                self.read_separator()

            # --------------------------------
            # Invalid Characters
            # --------------------------------

            else:

                raise LexerError(
                    f"Unexpected character '{char}' "
                    f"at line {start_line}, "
                    f"column {start_column}"
                )

        # Add EOF token
        self.add_token(
            "EOF",
            "",
            self.line,
            self.column
        )

        return self.tokens


# ==========================================
# 15. CONVENIENCE FUNCTION
# ==========================================

def tokenize(source_code: str) -> List[Token]:
    """Tokenizes source code and returns a token list."""

    lexer = Lexer(source_code)

    return lexer.tokenize()


# ==========================================
# 16. MANUAL TESTING
# ==========================================

if __name__ == "__main__":

    source_code = """
    int main(void) {

        int x = 10;
        int y = 20;

        // Calculate sum
        int result = x + y;

        if (result >= 30) {
            return result;
        }

        return 0;
    }
    """

    try:

        tokens = tokenize(source_code)

        print("\n========== LEXER OUTPUT ==========\n")

        for token in tokens:
            print(token)

        print("\n========== TOTAL TOKENS ==========")
        print(len(tokens))

    except LexerError as error:

        print("\nLEXICAL ERROR:")
        print(error)
