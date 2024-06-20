from lc.lexer import lex
from lc.parser import ParseContext, parse
from lc.structure import EvalContext


def execute(source: str, ctx: EvalContext | None = None, *, parser: ParseContext | None = None, output_raw=False):
    statements = lex(source)

    ctx = EvalContext() if ctx is None else ctx
    parser = ParseContext() if parser is None else parser

    expressions = list(filter(lambda e: e is not None,
                              (parse(parser.reset(statement), ctx) for statement in statements)))

    for k, expression in enumerate(expressions):
        if len(expressions) > 1:
            print(f'*** Statement #{k}')

        if output_raw or ctx.eval_step:
            print(str(expression))
            print('-> ', end='')

        print(str(expression := expression.evaluate(ctx)))

        while not expression.is_atomic(ctx):
            print('-> ' + str(expression := expression.evaluate(ctx)))
