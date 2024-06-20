from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    DOT = 0
    LAMBDA = 1
    COMMA = 2
    ARROW = 3
    VARIABLE = 4
    INT = 5
    LPAREN = 6
    RPAREN = 7
    LSQUARE = 8
    RSQUARE = 9
    PLUS = 10
    MINUS = 11
    STAR = 12
    SLASH = 13


@dataclass
class Token:
    source: str
    type: TokenType
    line: int
    col: int

    def location(self):
        """Return location as string."""
        return f'Line {self.line + 1}, col {self.col}'


def syntax_error(token: Token, expected: str, message: str | None = None):
    """Generate a SyntaxError from arguments."""
    return SyntaxError(f'{token.location()}: expected {expected}, got \'{token.source}\'.' +
                       (' ' + message if message is not None else ''))


constant_tokens: dict[str, TokenType] = {
    '.': TokenType.DOT,
    '\\': TokenType.LAMBDA,
    ',': TokenType.COMMA,
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '[': TokenType.LSQUARE,
    ']': TokenType.RSQUARE,
    '<-': TokenType.ARROW,
    '+': TokenType.PLUS,
    '-': TokenType.MINUS,
    '*': TokenType.STAR,
    '/': TokenType.SLASH,
}


def lex(source: str, line_number: int = 0) -> list[list[Token]]:
    """Transform input source into a list of statements."""
    statements: list[list[Token]] = []
    tokens: list[Token] = []
    col = 0
    pos = 0
    parens: list[str] = []  # contain expected CLOSING brackets
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
            if len(parens) != 0:
                raise SyntaxError(f'Line {line_number}, col {pos}: expected \'{parens.pop()}\', got end of input '
                                  f'(unbalanced brackets)')

            parens = []

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
                    parens.append(')')
                elif token.type == TokenType.LSQUARE:
                    parens.append(']')
                elif token.type in (TokenType.RPAREN, TokenType.RSQUARE):
                    if len(parens) == 0:
                        raise SyntaxError(
                            f'Line {token.line}, col {token.col}: unexpected \'{symbol}\' (no opening bracket found)')

                    if (need := parens.pop()) != token.source:
                        raise syntax_error(token, need, '(mismatching brackets)')

                break

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
        if len(parens) > 0:
            raise SyntaxError(
                f'Line {line_number}, col {pos}: expected \'{parens.pop()}\', got end of input (unbalanced brackets)')

        statements.append(tokens)

    return statements
