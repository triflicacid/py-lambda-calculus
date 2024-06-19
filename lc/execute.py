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

        if len(statements) > 1:
            print(f'*** Statement #{k + 1}')

        if output_raw or ctx.eval_step:
            print(str(expression))
            print('-> ', end='')

        print(str(expression := expression.evaluate(ctx)))

        while not expression.is_atomic(ctx):
            print('-> ' + str(expression := expression.evaluate(ctx)))
