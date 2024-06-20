from lc.lexer import Token, TokenType
from lc.structure import Function, Argument, Expression, Variable, Integer, Application, BinaryOperation, EvalContext, \
    UnaryOperation


class ParseContext:
    """Contains data used in parsing."""
    def __init__(self, tokens: list[Token] | None = None):
        self.tokens = [] if tokens is None else tokens
        self.pos = 0
        self.args: list[str] = []  # record symbols used as function arguments

    def reset(self, tokens: list[Token] | None = None):
        """Reset object, updating token list if necessary, and return self."""
        self.pos = 0

        if tokens is not None:
            self.tokens = tokens

        return self

    def get(self, offset: int = 0):
        """Get the token at `self.pos`, otherwise return None."""
        pos = self.pos + offset
        return self.tokens[pos] if 0 <= pos < len(self.tokens) else None

    def prev(self):
        """Equivalent to `self.get(-1)`, but assumes this location exists."""
        return self.tokens[self.pos - 1]

    def move(self, offset: int):
        """Move `self.pos` by `offset`."""
        self.pos += offset

    def eof(self):
        """Return if no more tokens left to consume."""
        return self.pos >= len(self.tokens)

    def expect(self, *types: TokenType, offset=0, advance=True, raise_error=False, error_expected: str | None = None):
        """Return True and advance `self.pos` if `self.get()`'s type is in `types`, otherwise return False."""
        if (token := self.get(offset)) is not None and token.type in types:
            if advance:
                self.pos += 1

            return True

        if raise_error:
            raise SyntaxError(f'{token.location()}: expected {error_expected}, got \'{token.source}\'')

        return False

    def is_arg(self, symbol: str):
        return symbol in self.args

    def push_arg(self, arg: Argument):
        self.args.append(str(arg))

    def pop_arg(self):
        self.args.pop()


def syntax_error(token: Token, expected: str, message: str | None = None):
    """Generate a SyntaxError from arguments."""
    return SyntaxError(f'{token.location()}: expected {expected}, got \'{token.source}\'.' +
                       (' ' + message if message is not None else ''))


def parse_function(parser: ParseContext) -> Function:
    """Parse a function definition."""
    parser.expect(TokenType.LAMBDA, raise_error=True, error_expected='\\')

    function_token = parser.prev()

    # function argument
    parser.expect(TokenType.VARIABLE, raise_error=True, error_expected='argument')

    argument = Argument(parser.prev())

    parser.expect(TokenType.DOT, raise_error=True, error_expected='.')

    # parse function body
    parser.push_arg(argument)
    body = parse_expression(parser)
    parser.pop_arg()

    return Function(function_token, argument, body)


def parse_binary_operator(parser: ParseContext) -> str:
    """Parse a binary operator symbol."""
    parser.expect(TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
                  raise_error=True, error_expected='\'+\', \'-\', \'*\', \'/\' (operator)')
    return parser.prev().source


def parse_group(parser: ParseContext) -> Expression:
    """Parse a group `(...)`."""
    parser.expect(TokenType.LPAREN, raise_error=True, error_expected='(')

    # parse group body
    expr = parse_expression(parser)

    parser.expect(TokenType.RPAREN, raise_error=True, error_expected=')')
    return expr


def parse_unit(parser: ParseContext, allow_args=False) -> Expression:
    """Parse a single unit: variable, integer, function. Argument dictates if application args are allowed."""
    expr: Expression

    if parser.expect(TokenType.LAMBDA, advance=False):
        expr = parse_function(parser)
    elif parser.expect(TokenType.VARIABLE):
        expr = Argument(token) if (token := parser.prev()).source in parser.args else Variable(token)
    elif parser.expect(TokenType.MINUS):
        if parser.expect(TokenType.INT):
            expr = Integer(parser.prev()).negate()
        else:
            op = parser.prev()
            expr = UnaryOperation(op, parse_unit(parser, allow_args=True))
    elif parser.expect(TokenType.INT):
        expr = Integer(parser.prev())
    elif parser.expect(TokenType.LPAREN, advance=False):
        expr = parse_group(parser)
    else:
        raise syntax_error(parser.get(), '\'\\\', variable, \'(\', or integer')

    # parse applied arguments
    if allow_args:
        while parser.expect(TokenType.LAMBDA, TokenType.VARIABLE, TokenType.INT, TokenType.LPAREN, advance=False):
            argument = parse_unit(parser)
            expr = expr.apply_argument(argument)

    return expr


def parse_expression(parser: ParseContext) -> Expression:
    """Parse an expression; a combination of units and operators."""
    lhs = parse_unit(parser, allow_args=True)

    # end of expression?
    if parser.eof() or parser.expect(TokenType.RPAREN, advance=False):
        return lhs

    parse_binary_operator(parser)
    op = parser.prev()

    rhs = parse_expression(parser)

    return BinaryOperation(op, lhs, rhs)


def parse(parser: ParseContext, ctx: EvalContext) -> Expression | None:
    """Parse token list of one statement into an expression."""
    parser.reset()

    # check for assignment
    symbol: Token | None = None

    if parser.expect(TokenType.VARIABLE, advance=False) and parser.expect(TokenType.ARROW, offset=1, advance=False):
        symbol = parser.get()
        parser.move(2)

    # parse expression
    expr = parse_expression(parser)

    # this should be all...
    if not parser.eof():
        raise syntax_error(parser.get(), 'end of statement')

    # if a plain expression (no assignment), return
    if symbol is None:
        return expr

    # forbid overwriting values
    if symbol.source in ctx.bound:
        raise NameError(f'{symbol.location()}: attempted assignment to bound name \'{symbol.source}\'')

    # bind value to symbol
    ctx.bound[symbol.source] = expr

    return None
