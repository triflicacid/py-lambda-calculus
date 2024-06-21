from sys import argv

from lc.execute import execute
from lc.parser import ParseContext
from lc.structure import EvalContext

if __name__ == "__main__":
    filepath: str | None = None
    output_raw = False
    ctx = EvalContext()
    parser = ParseContext()

    for arg in argv[1:]:
        if arg == "--output-raw" and not output_raw:
            output_raw = True
        elif arg == "--no-force-eval" and ctx.force_eval:
            ctx.force_eval = False
        elif arg == "--no-eval-ops" and ctx.eval_ops:
            ctx.eval_ops = False
        elif arg == "--eval-step" and not ctx.eval_step:
            ctx.eval_step = True
        elif arg == "--allow-multi-args" and not parser.multi_args:
            parser.multi_args = True
        elif filepath is None:
            filepath = arg
        else:
            raise ValueError(f'Unknown or repeated argument {arg}')

    if filepath is None:
        raise ValueError(f'Expected filepath to be provided')

    with open(filepath, 'r') as file:
        execute(
            file.read(),
            ctx,
            output_raw=output_raw,
            parser=parser
        )
