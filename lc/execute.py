from lc.lexer import lex
from lc.parser import ParseContext, parse
from lc.structure import EvalContext


def remove_outer_brackets(s: str):
    """Remove any outer-level brackets."""
    # should only have one level, due to how .__str__ works on Expressions.
    # might be nice to strip and n>0 pairs of outer brackets, but must check they match first.
    if s[0] == '(' and s[-1] == ')':
        return s[1:-1]

    return s


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

        print(remove_outer_brackets(str(expression := expression.evaluate(ctx))))

        while not expression.is_atomic(ctx):
            print('-> ' + remove_outer_brackets(str(expression := expression.evaluate(ctx))))
