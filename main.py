from lc.execute import execute
from lc.structure import EvalContext

if __name__ == "__main__":
    filepath = "./example.lc"

    ctx = EvalContext()
    ctx.eval_step = True
    ctx.force_eval = False

    with open(filepath, 'r') as file:
        execute(file.read(), ctx)
