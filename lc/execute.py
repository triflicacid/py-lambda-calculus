from lc.lexer import lex
from lc.parser import ParseContext, parse
from lc.structure import EvalContext


def execute(source: str, ctx: EvalContext | None = None, *, parser: ParseContext | None = None, output_raw=False):
    statements = lex(source)

    ctx = EvalContext() if ctx is None else ctx
    parser = ParseContext() if parser is None else parser

    for k, statement in enumerate(statements):
        parser.reset(statement)
        expression = parse(parser)

        print(f'*** Statement #{k + 1}')

        if output_raw:
            print(str(expression))
            print('-> ', end='')

        print(str(expression.evaluate(ctx)))