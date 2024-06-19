from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    DOT = 1
    LAMBDA = 2
    VARIABLE = 3
    INT = 4
    LPAREN = 5
    RPAREN = 6
    PLUS = 7


@dataclass
class Token:
    source: str
    type: TokenType
    line: int
    col: int

    def location(self):
        """Return location as string."""
        return f'Line {self.line + 1}, col {self.col}'


constant_tokens: dict[str, TokenType] = {
    '.': TokenType.DOT,
    '\\': TokenType.LAMBDA,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '+': TokenType.PLUS,
}


def lex(source: str, line_number: int = 0) -> list[list[Token]]:
    """Transform input source into a list of statements."""
    statements: list[list[Token]] = []
    tokens: list[Token] = []
    col = 0
    pos = 0
    parens = 0
    in_comment = False

    while pos < len(source):
        # eat newline
        if source[pos] == '\n' or (source[pos] == '\r' and source[pos + 1] == '\n'):
            in_comment = False
            line_number += 1
            col = 0

            # add current statement to list
            if len(tokens) > 0:
                statements.append(tokens)
                tokens = []

            pos += 1 if source[pos] == '\n' else 2

            # reset paren counter for new statement
            if parens != 0:
                raise SyntaxError(
                    f'Line {line_number}, col {pos}: expected \'(\', got end of input (unbalanced brackets)')

            parens = 0

            continue

        # if we are in a comment, skip
        if in_comment:
            pos += 1
            continue

        # eat whitespace
        if source[pos].isspace():
            pos += 1
            col += 1
            continue

        # comment?
        if source[pos] == '#':
            in_comment = True
            pos += 1
            continue

        # semicolon?
        if source[pos] == ';':
            if len(tokens) > 0:
                statements.append(tokens)
                tokens = []

            pos += 1
            continue

        # attempt to parse input from current position into `token`
        token: Token | None = None

        # scan for a constant token
        for symbol in constant_tokens:
            if source[pos:pos+len(symbol)] == symbol:
                token = Token(symbol, constant_tokens[symbol], line_number, col)
                pos += len(symbol)
                col += len(symbol)

                if token.type == TokenType.LPAREN:
                    parens += 1
                elif token.type == TokenType.RPAREN:
                    if parens == 0:
                        raise SyntaxError(
                            f'Line {token.line}, col {token.col}: unexpected \')\' (no opening bracket found)')

                    parens -= 1

        # scan for a variable
        if token is None and source[pos].islower():
            token = Token('', TokenType.VARIABLE, line_number, col)

            while pos < len(source) and source[pos].islower():
                token.source += source[pos]
                pos += 1
                col += 1

        # scan for an integer
        if token is None and source[pos].isnumeric():
            token = Token('', TokenType.INT, line_number, col)

            while pos < len(source) and source[pos].isnumeric():
                token.source += source[pos]
                pos += 1
                col += 1

        # if no token has been parsed: error
        if token is None:
            raise SyntaxError(f'Line {line_number}, col {pos}: unexpected character \'{source[pos]}\'')

        # add to list of parsed tokens
        tokens.append(token)

    # if tokens remain, add as new statement
    if len(tokens) > 0 and (len(statements) == 0 or statements[-1] is not tokens):
        if parens != 0:
            raise SyntaxError(f'Line {line_number}, col {pos}: expected \'(\', got end of input (unbalanced brackets)')

        statements.append(tokens)

    return statements
